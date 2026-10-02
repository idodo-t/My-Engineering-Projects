# My Engineering Projects

I use this repository to share runnable implementations for the engineering projects presented on my portfolio. The eight folders below contain functional reference implementations created from project summaries; they are not claimed to be the original source code or to reproduce unavailable datasets, weights, or historical results. The library application's original source is linked separately.

## Artificial Intelligence

### Malware Detection with CNN

I built a 1D CNN training and prediction pipeline for binary numeric malware-feature data, including input validation, a stratified holdout, safe model serialization, and a CSV prediction command.

**Code:** [malware-detection](./malware-detection/) · **Technologies:** PyTorch, scikit-learn, Pandas

The original feature dataset is not included, so this implementation does not claim to reproduce the 96% result from my project summary.

### Nutrition Detection with Computer Vision

I added a YOLO training and inference pipeline for an Ultralytics-format image dataset. The class names and dataset paths must be supplied for the actual labeled images.

**Code:** [nutrition-detection](./nutrition-detection/) · **Technologies:** YOLO, Python

The original images, annotations, and weights are not included, so this implementation does not claim to reproduce the 92% result from my project summary.

### Agentic AI and RAG Conversational Assistant

I built a document retriever with source-aware answers, session memory, and an optional OpenAI-compatible generation endpoint. It runs in offline retrieval mode without an API key.

**Code:** [agentic-rag-assistant](./agentic-rag-assistant/) · **Technologies:** Python, TF-IDF, RAG, optional LLM API

## Data and Connected Systems

### Hotel Occupancy Forecasting

I built a time-series baseline using lag features and a chronological holdout, with a command to forecast future occupancy and an explicitly synthetic demo-data generator.

**Code:** [hotel-occupancy-forecast](./hotel-occupancy-forecast/) · **Technologies:** Python, Pandas, scikit-learn

### BI / ETL Data Warehouse and Dashboards

I built a validated CSV-to-SQLite ETL pipeline, star schema, aggregate queries, and a local HTML dashboard.

**Code:** [bi-etl-warehouse](./bi-etl-warehouse/) · **Technologies:** Python, SQLite, HTML

### Real-Time IoT Dashboard

I built an MQTT subscriber with payload validation, latest-reading storage, an HTTP JSON endpoint, and a browser dashboard. A demo mode runs without a broker and uses clearly synthetic values.

**Code:** [iot-dashboard](./iot-dashboard/) · **Technologies:** Python, MQTT, HTTP

## Software Engineering and Security

### Library Management System

I built a NoSQL library application for books, members, loans, returns, and statistics.

**Original source:** [idodo-t/library_management_system](https://github.com/idodo-t/library_management_system) · **Technologies:** Python, Flask, MongoDB, Bootstrap

### Linux Server Hardening

I built a read-only audit for selected SSH settings and sensitive account-file permissions. It reports findings and recommendations without modifying the host.

**Code:** [linux-hardening](./linux-hardening/) · **Technologies:** Python, Linux

### Medical Appointment Booking Platform

I built a .NET 9 API for appointment creation, listing, cancellation, JSON persistence, and preventing clinician schedule conflicts.

**Code:** [medical-appointment-booking](./medical-appointment-booking/) · **Technologies:** C#, .NET 9

This is a local demonstration, not a production medical system; it has no authentication or clinical-data protections.

## Run and Test

Each project folder has its own README with setup and run commands. Python projects use `python -m unittest discover -s tests -v`; the appointment API builds with `dotnet build`.

On Windows with Python and the .NET 9 SDK installed, run all suites and compile checks with `./scripts/test_all.ps1`.

For more project details, visit [my portfolio](https://portfolio-react-bice-tau-78.vercel.app/).