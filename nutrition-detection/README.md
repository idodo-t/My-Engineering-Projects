# Nutrition Detection with Computer Vision

I created a YOLO training and inference pipeline for food-item and nutritional-value image detection.

## Requirements

- Python 3.10 or newer
- A labeled dataset in Ultralytics YOLO detection format
- A compatible Ultralytics checkpoint or internet access to download the default model

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Dataset

Copy `data.yaml.example` to `data.yaml`, set the dataset root, and replace the example class name with the labels used by your annotations. A typical dataset contains `images/train`, `images/val`, `labels/train`, and `labels/val` under that root.

## Train

```bash
python train.py data.yaml --model yolov8n.pt --epochs 50 --image-size 640
```

The best weights are written under `runs/nutrition/nutrition-detection/weights/best.pt`.

## Predict

```bash
python predict.py path/to/image.jpg --weights runs/nutrition/nutrition-detection/weights/best.pt
```

Annotated outputs are saved under `runs/predictions/nutrition-detection`.

## Results

The original labeled images, annotations, and trained weights are not included here. This repository provides the runnable pipeline, but it does not reproduce or claim the 92% result reported for the original project.
