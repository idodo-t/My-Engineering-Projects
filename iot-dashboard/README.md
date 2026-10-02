# Real-Time IoT Dashboard

I built a small MQTT subscriber and local web dashboard for sensor readings. The service validates incoming JSON, keeps the latest reading per device, and exposes both an HTML dashboard and a JSON endpoint.

## Requirements

- Python 3.10 or newer
- For MQTT mode: an MQTT broker and `paho-mqtt`

```bash
python -m pip install -r requirements.txt
```

Start the dashboard with a clearly synthetic reading:

```bash
python mqtt_dashboard.py --demo
```

Open `http://127.0.0.1:8080/`. For a real broker:

```bash
python mqtt_dashboard.py --mqtt-host 127.0.0.1 --topic 'sensors/+/telemetry'
```

Publish JSON payloads such as `{"device_id":"sensor-1","temperature_c":21.5,"humidity_pct":45}` to a matching topic. The API is available at `/api/latest`; `/health` reports service status.

The dashboard is a functional integration example. The demo sensor values are synthetic, and a real broker/device network is not included.

Run tests with `python -m unittest discover -s tests -v`.
