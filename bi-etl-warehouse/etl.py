import argparse
import csv
import math
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path

REQUIRED_COLUMNS = {"sale_date", "region", "product", "quantity", "revenue"}


def read_sales(path: str | Path) -> list[dict]:
    with Path(path).open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
            raise ValueError(f"CSV must contain columns: {', '.join(sorted(REQUIRED_COLUMNS))}")
        rows = []
        for line_number, raw in enumerate(reader, start=2):
            try:
                sale_date = date.fromisoformat(raw["sale_date"].strip())
                region = raw["region"].strip()
                product = raw["product"].strip()
                quantity = int(raw["quantity"])
                revenue = float(raw["revenue"])
            except (AttributeError, TypeError, ValueError) as error:
                raise ValueError(f"Invalid value on CSV line {line_number}") from error
            if not region or not product or quantity <= 0 or not math.isfinite(revenue) or revenue < 0:
                raise ValueError(f"Invalid business values on CSV line {line_number}")
            rows.append({"date": sale_date, "region": region, "product": product, "quantity": quantity, "revenue": revenue})
    if not rows:
        raise ValueError("CSV contains no sales rows")
    return rows


def create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS dim_date (
            date_key INTEGER PRIMARY KEY,
            full_date TEXT NOT NULL UNIQUE,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            day INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS dim_region (
            region_id INTEGER PRIMARY KEY,
            region_name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS dim_product (
            product_id INTEGER PRIMARY KEY,
            product_name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS fact_sales (
            sale_id INTEGER PRIMARY KEY,
            date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
            region_id INTEGER NOT NULL REFERENCES dim_region(region_id),
            product_id INTEGER NOT NULL REFERENCES dim_product(product_id),
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            revenue REAL NOT NULL CHECK (revenue >= 0)
        );
        CREATE INDEX IF NOT EXISTS idx_fact_sales_date ON fact_sales(date_key);
        CREATE INDEX IF NOT EXISTS idx_fact_sales_region ON fact_sales(region_id);
        """
    )


def run_etl(csv_path: str | Path, database_path: str | Path) -> dict[str, float | int]:
    rows = read_sales(csv_path)
    db_path = Path(database_path).expanduser()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db_path)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        create_schema(connection)
        with connection:
            connection.execute("DELETE FROM fact_sales")
            for row in rows:
                sale_date = row["date"]
                connection.execute(
                    "INSERT OR IGNORE INTO dim_date VALUES (?, ?, ?, ?, ?)",
                    (int(sale_date.strftime("%Y%m%d")), sale_date.isoformat(), sale_date.year, sale_date.month, sale_date.day),
                )
                connection.execute("INSERT OR IGNORE INTO dim_region(region_name) VALUES (?)", (row["region"],))
                connection.execute("INSERT OR IGNORE INTO dim_product(product_name) VALUES (?)", (row["product"],))
                date_key = int(sale_date.strftime("%Y%m%d"))
                region_id = connection.execute("SELECT region_id FROM dim_region WHERE region_name = ?", (row["region"],)).fetchone()[0]
                product_id = connection.execute("SELECT product_id FROM dim_product WHERE product_name = ?", (row["product"],)).fetchone()[0]
                connection.execute(
                    "INSERT INTO fact_sales(date_key, region_id, product_id, quantity, revenue) VALUES (?, ?, ?, ?, ?)",
                    (date_key, region_id, product_id, row["quantity"], row["revenue"]),
                )
    return summarize(database_path)


def summarize(database_path: str | Path) -> dict:
    with closing(sqlite3.connect(database_path)) as connection:
        connection.row_factory = sqlite3.Row
        totals = connection.execute(
            "SELECT COUNT(*) AS sale_count, COALESCE(SUM(revenue), 0) AS revenue, "
            "COALESCE(AVG(revenue), 0) AS average_sale FROM fact_sales"
        ).fetchone()
        regions = connection.execute(
            "SELECT r.region_name AS region, SUM(f.revenue) AS revenue, SUM(f.quantity) AS units "
            "FROM fact_sales f JOIN dim_region r USING(region_id) GROUP BY r.region_name ORDER BY revenue DESC"
        ).fetchall()
    return {
        "sale_count": int(totals["sale_count"]),
        "revenue": round(float(totals["revenue"]), 2),
        "average_sale": round(float(totals["average_sale"]), 2),
        "by_region": [dict(row) for row in regions],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Load CSV sales into a SQLite star-schema warehouse")
    parser.add_argument("--input", default="data/sales_sample.csv")
    parser.add_argument("--db", default="warehouse.db")
    args = parser.parse_args()
    result = run_etl(args.input, args.db)
    print(f"Loaded {result['sale_count']} sales; revenue={result['revenue']:.2f}; database={args.db}")


if __name__ == "__main__":
    main()
