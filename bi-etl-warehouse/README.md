# BI / ETL Data Warehouse

I built a small ETL pipeline that validates CSV sales, loads a SQLite star schema, and serves a local business-intelligence dashboard.

## Run

This project uses only the Python standard library.

```bash
python etl.py --input data/sales_sample.csv --db warehouse.db
python dashboard.py --db warehouse.db --host 127.0.0.1 --port 8080
```

Open `http://127.0.0.1:8080/` for the dashboard or `/api/summary` for JSON.

The warehouse contains date, region, and product dimensions plus a sales fact table. Loading replaces the fact rows transactionally while preserving dimension keys, so rerunning the same input is idempotent.

`data/sales_sample.csv` contains synthetic demo data, not real business records. Replace it with a CSV containing `sale_date`, `region`, `product`, `quantity`, and `revenue` before using the output for decisions.

Run tests with `python -m unittest discover -s tests -v`.
