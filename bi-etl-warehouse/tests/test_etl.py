import csv
import tempfile
import unittest
from pathlib import Path

from etl import run_etl, summarize
from dashboard import render_dashboard


class EtlTests(unittest.TestCase):
    def write_sales(self, path: Path) -> None:
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=["sale_date", "region", "product", "quantity", "revenue"])
            writer.writeheader()
            writer.writerows(
                [
                    {"sale_date": "2025-01-01", "region": "North", "product": "Tea", "quantity": 2, "revenue": 12.5},
                    {"sale_date": "2025-01-02", "region": "South", "product": "Coffee", "quantity": 1, "revenue": 9.0},
                ]
            )

    def test_etl_is_idempotent_and_dashboard_renders(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            csv_path, db_path = root / "sales.csv", root / "warehouse.db"
            self.write_sales(csv_path)
            first = run_etl(csv_path, db_path)
            second = run_etl(csv_path, db_path)
            html = render_dashboard(db_path)

            self.assertEqual(first["sale_count"], 2)
            self.assertEqual(second["sale_count"], 2)
            self.assertEqual(second["revenue"], 21.5)
            self.assertIn("Sales Warehouse", html)
            self.assertIn("North", html)

    def test_rejects_negative_revenue(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            csv_path = root / "bad.csv"
            self.write_sales(csv_path)
            content = csv_path.read_text(encoding="utf-8").replace(",1,9.0", ",1,-9.0")
            csv_path.write_text(content, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "business values"):
                run_etl(csv_path, root / "warehouse.db")


if __name__ == "__main__":
    unittest.main()
