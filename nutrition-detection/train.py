import argparse
from pathlib import Path


def validate_data_yaml(path: str | Path) -> Path:
    data_path = Path(path).expanduser().resolve()
    if not data_path.is_file():
        raise FileNotFoundError(f"YOLO dataset YAML not found: {data_path}")
    if data_path.suffix.lower() not in {".yaml", ".yml"}:
        raise ValueError("Dataset configuration must use a .yaml or .yml file")
    return data_path


def train_detector(
    data_yaml: str | Path,
    model_name: str = "yolov8n.pt",
    epochs: int = 50,
    image_size: int = 640,
    output_dir: str | Path = "runs/nutrition",
):
    if epochs < 1 or image_size < 32:
        raise ValueError("epochs must be positive and image_size must be at least 32")
    data_path = validate_data_yaml(data_yaml)
    try:
        from ultralytics import YOLO
    except ImportError as error:
        raise RuntimeError("Install project dependencies with: pip install -r requirements.txt") from error

    model = YOLO(model_name)
    return model.train(
        data=str(data_path),
        epochs=epochs,
        imgsz=image_size,
        project=str(output_dir),
        name="nutrition-detection",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Train YOLOv8 on a labeled food-image dataset")
    parser.add_argument("data", help="Path to the dataset YAML")
    parser.add_argument("--model", default="yolov8n.pt", help="Ultralytics model or checkpoint")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--image-size", type=int, default=640)
    parser.add_argument("--output-dir", default="runs/nutrition")
    args = parser.parse_args()
    train_detector(args.data, args.model, args.epochs, args.image_size, args.output_dir)


if __name__ == "__main__":
    main()
