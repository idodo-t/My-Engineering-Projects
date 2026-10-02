import tempfile
import unittest
from pathlib import Path

import pandas as pd

from forecast import forecast_next_days, load_history, train_forecaster
from generate_sample import write_sample


class HotelForecastTests(unittest.TestCase):
    def test_train_and_forecast(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            csv_path = root / "synthetic.csv"
            model_path = root / "occupancy.joblib"
            write_sample(csv_path, days=100)
            metrics = train_forecaster(csv_path, model_path)
            result = forecast_next_days(model_path, days=5)

            self.assertTrue(model_path.exists())
            self.assertGreaterEqual(metrics["holdout_mae"], 0)
            self.assertEqual(len(result), 5)
            self.assertTrue(result["predicted_occupancy_rate"].between(0, 100).all())
            self.assertEqual(result.iloc[0]["date"], "2025-04-11")

    def test_rejects_non_consecutive_dates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gapped.csv"
            dates = pd.date_range("2025-01-01", periods=50).delete(10)
            pd.DataFrame({"date": dates, "occupancy_rate": [60] * len(dates)}).to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "consecutive"):
                load_history(path)


if __name__ == "__main__":
    unittest.main()
