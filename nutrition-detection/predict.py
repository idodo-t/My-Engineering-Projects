import argparse
from pathlib import Path


def predict_images(
    weights: str | Path,
    source: str | Path,
    output_dir: str | Path = "runs/predictions",
    confidence: float = 0.25,
):
    weights_path = Path(weights).expanduser().resolve()
    source_path = Path(source).expanduser().resolve()
    if not weights_path.is_file():
        raise FileNotFoundError(f"Model weights not found: {weights_path}")
    if not source_path.exists():
        raise FileNotFoundError(f"Image source not found: {source_path}")
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be between 0 and 1")
    try:
        from ultralytics import YOLO
    except ImportError as error:
        raise RuntimeError("Install project dependencies with: pip install -r requirements.txt") from error

    model = YOLO(str(weights_path))
    return model.predict(
        source=str(source_path),
        conf=confidence,
        save=True,
        project=str(output_dir),
        name="nutrition-detection",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run food-image detection with a trained YOLO model")
    parser.add_argument("source", help="Image file or directory")
    parser.add_argument("--weights", default="runs/nutrition/nutrition-detection/weights/best.pt")
    parser.add_argument("--output-dir", default="runs/predictions")
    parser.add_argument("--confidence", type=float, default=0.25)
    args = parser.parse_args()
    predict_images(args.weights, args.source, args.output_dir, args.confidence)


if __name__ == "__main__":
    main()
