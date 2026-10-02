import argparse
import csv
import math
from datetime import date, timedelta
from pathlib import Path


def write_sample(path: str | Path, days: int = 180) -> None:
    if days < 45:
        raise ValueError("At least 45 rows are needed for the forecast demo")
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    start = date(2025, 1, 1)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["date", "occupancy_rate"])
        for index in range(days):
            current = start + timedelta(days=index)
            seasonal = 8 * math.sin(2 * math.pi * index / 90)
            weekend = 6 if current.weekday() >= 4 else 0
            occupancy = min(95, max(20, 62 + seasonal + weekend))
            writer.writerow([current.isoformat(), round(occupancy, 2)])


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate clearly synthetic demo occupancy data")
    parser.add_argument("--output", default="data/synthetic_occupancy.csv")
    parser.add_argument("--days", type=int, default=180)
    args = parser.parse_args()
    write_sample(args.output, args.days)
    print(f"Wrote synthetic demo data: {args.output}")


if __name__ == "__main__":
    main()
