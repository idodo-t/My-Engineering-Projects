import argparse
from datetime import timedelta
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

LAGS = (1, 7, 14, 28)
FEATURE_COLUMNS = [
    *(f"lag_{lag}" for lag in LAGS),
    "day_of_week",
    "day_of_year_sin",
    "day_of_year_cos",
]


def load_history(csv_path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(csv_path)
    required = {"date", "occupancy_rate"}
    if not required.issubset(frame.columns):
        raise ValueError("CSV must contain date and occupancy_rate columns")
    frame = frame[["date", "occupancy_rate"]].copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    frame["occupancy_rate"] = pd.to_numeric(frame["occupancy_rate"], errors="raise")
    frame = frame.sort_values("date").reset_index(drop=True)
    if frame["date"].duplicated().any():
        raise ValueError("Each date must appear only once")
    if not frame["occupancy_rate"].between(0, 100).all():
        raise ValueError("occupancy_rate must be a percentage between 0 and 100")
    if len(frame) < 45:
        raise ValueError("At least 45 daily observations are required for the 28-day lags")
    if frame["date"].diff().dropna().dt.days.ne(1).any():
        raise ValueError("Dates must be consecutive daily observations")
    return frame


def build_features(history: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    work = history.copy()
    for lag in LAGS:
        work[f"lag_{lag}"] = work["occupancy_rate"].shift(lag)
    day_of_year = work["date"].dt.dayofyear
    work["day_of_week"] = work["date"].dt.dayofweek
    work["day_of_year_sin"] = np.sin(2 * np.pi * day_of_year / 365.25)
    work["day_of_year_cos"] = np.cos(2 * np.pi * day_of_year / 365.25)
    usable = work.dropna(subset=FEATURE_COLUMNS)
    return usable[FEATURE_COLUMNS], usable["occupancy_rate"]


def train_forecaster(csv_path: str | Path, model_path: str | Path) -> dict[str, float]:
    history = load_history(csv_path)
    features, target = build_features(history)
    split = int(len(features) * 0.8)
    if split < 2 or split >= len(features):
        raise ValueError("Not enough feature rows for a chronological holdout")

    evaluation_model = RandomForestRegressor(n_estimators=120, min_samples_leaf=2, random_state=42, n_jobs=-1)
    evaluation_model.fit(features.iloc[:split], target.iloc[:split])
    holdout_prediction = evaluation_model.predict(features.iloc[split:])
    mae = float(mean_absolute_error(target.iloc[split:], holdout_prediction))

    final_model = RandomForestRegressor(n_estimators=120, min_samples_leaf=2, random_state=42, n_jobs=-1)
    final_model.fit(features, target)
    output = Path(model_path).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": final_model, "history": history, "holdout_mae": mae}, output)
    return {"holdout_mae": mae, "holdout_rows": float(len(target) - split)}


def forecast_next_days(model_path: str | Path, days: int = 7) -> pd.DataFrame:
    if days < 1 or days > 90:
        raise ValueError("days must be between 1 and 90")
    checkpoint = joblib.load(model_path)
    model = checkpoint["model"]
    history: pd.DataFrame = checkpoint["history"].copy()
    values = history["occupancy_rate"].astype(float).tolist()
    next_date = history["date"].iloc[-1]
    forecasts = []

    for _ in range(days):
        next_date = next_date + timedelta(days=1)
        day_of_year = next_date.dayofyear
        row = {f"lag_{lag}": values[-lag] for lag in LAGS}
        row.update(
            {
                "day_of_week": next_date.dayofweek,
                "day_of_year_sin": np.sin(2 * np.pi * day_of_year / 365.25),
                "day_of_year_cos": np.cos(2 * np.pi * day_of_year / 365.25),
            }
        )
        prediction = float(np.clip(model.predict(pd.DataFrame([row], columns=FEATURE_COLUMNS))[0], 0, 100))
        values.append(prediction)
        forecasts.append({"date": next_date.date().isoformat(), "predicted_occupancy_rate": round(prediction, 2)})
    return pd.DataFrame(forecasts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and forecast daily hotel occupancy")
    commands = parser.add_subparsers(dest="command", required=True)
    train_parser = commands.add_parser("train")
    train_parser.add_argument("csv")
    train_parser.add_argument("--model", default="artifacts/occupancy.joblib")
    predict_parser = commands.add_parser("predict")
    predict_parser.add_argument("--model", default="artifacts/occupancy.joblib")
    predict_parser.add_argument("--days", type=int, default=7)
    predict_parser.add_argument("--output", default="forecast.csv")
    args = parser.parse_args()

    if args.command == "train":
        metrics = train_forecaster(args.csv, args.model)
        print(f"Chronological holdout MAE: {metrics['holdout_mae']:.2f} percentage points")
        print(f"Saved model: {args.model}")
    else:
        result = forecast_next_days(args.model, args.days)
        result.to_csv(args.output, index=False)
        print(f"Saved {len(result)} forecast rows: {args.output}")


if __name__ == "__main__":
    main()
