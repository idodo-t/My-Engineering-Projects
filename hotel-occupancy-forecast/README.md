# Hotel Occupancy Forecasting

I built a time-series baseline that forecasts daily room occupancy from historical occupancy rates. It uses lagged observations, weekday, and annual seasonality, with a chronological holdout to avoid random time-series leakage.

## Requirements

- Python 3.10 or newer
- CSV columns: `date` (daily ISO date) and `occupancy_rate` (percentage from 0 to 100)
- At least 45 consecutive daily observations

```bash
python -m pip install -r requirements.txt
python generate_sample.py
python forecast.py train data/synthetic_occupancy.csv
python forecast.py predict --days 14 --output forecast.csv
```

`generate_sample.py` creates deterministic **synthetic demo data**. Replace it with real historical hotel data before interpreting a forecast. The model reports mean absolute error on a chronological holdout and saves its checkpoint under `artifacts/`.

The synthetic demo is only for exercising the pipeline; it does not reproduce or validate any result from a real hotel dataset.

Run tests with `python -m unittest discover -s tests -v`.
