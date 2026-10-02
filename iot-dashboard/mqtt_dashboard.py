import argparse
import json
import logging
import math
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LOGGER = logging.getLogger(__name__)


class DeviceStore:
    def __init__(self) -> None:
        self._latest: dict[str, dict] = {}
        self._lock = threading.Lock()

    def update(self, payload: bytes | str | dict) -> dict:
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError as error:
                raise ValueError("MQTT payload must be valid JSON") from error
        if not isinstance(payload, dict):
            raise ValueError("MQTT payload must be a JSON object")

        device_id = str(payload.get("device_id", "")).strip()
        if not device_id or len(device_id) > 80:
            raise ValueError("device_id must contain 1 to 80 characters")
        try:
            temperature = float(payload["temperature_c"])
            humidity = float(payload["humidity_pct"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("temperature_c and humidity_pct must be numeric") from error
        if not math.isfinite(temperature) or not -80 <= temperature <= 100:
            raise ValueError("temperature_c must be between -80 and 100")
        if not math.isfinite(humidity) or not 0 <= humidity <= 100:
            raise ValueError("humidity_pct must be between 0 and 100")
        recorded_at = str(payload.get("recorded_at") or datetime.now(timezone.utc).isoformat())
        reading = {
            "device_id": device_id,
            "temperature_c": round(temperature, 2),
            "humidity_pct": round(humidity, 2),
            "recorded_at": recorded_at,
        }
        with self._lock:
            self._latest[device_id] = reading
        return reading

    def latest(self) -> list[dict]:
        with self._lock:
            return [self._latest[key].copy() for key in sorted(self._latest)]


def make_handler(store: DeviceStore):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/health":
                body = json.dumps({"status": "ok"}).encode("utf-8")
                content_type = "application/json; charset=utf-8"
            elif self.path == "/api/latest":
                body = json.dumps({"readings": store.latest()}).encode("utf-8")
                content_type = "application/json; charset=utf-8"
            elif self.path == "/":
                body = DASHBOARD_HTML.encode("utf-8")
                content_type = "text/html; charset=utf-8"
            else:
                body = b"Not found"
                self.send_response(404)
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:
            return

    return Handler


DASHBOARD_HTML = """<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>IoT Sensor Dashboard</title>
<style>
body{font:16px system-ui,sans-serif;max-width:960px;margin:40px auto;padding:0 20px;background:#f2f7f6;color:#142b2a}
h1{font-size:2rem}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}
article{padding:20px;background:white;border:1px solid #d7e4e1;border-radius:8px}strong{display:block;font-size:1.7rem;margin-top:12px}
small{color:#596b68}#status{color:#087f5b}
</style>
<h1>IoT Sensor Dashboard</h1><p id="status">Waiting for readings…</p><section id="readings" class="grid"></section>
<script>
async function refresh(){
  const response=await fetch('/api/latest');
  const data=await response.json();
  const root=document.getElementById('readings');
  root.replaceChildren();
  for(const reading of data.readings){
    const card=document.createElement('article');
    const title=document.createElement('h2'); title.textContent=reading.device_id;
    const temperature=document.createElement('strong'); temperature.textContent=`${reading.temperature_c} °C`;
    const humidity=document.createElement('strong'); humidity.textContent=`${reading.humidity_pct}% humidity`;
    const time=document.createElement('small'); time.textContent=`Updated ${reading.recorded_at}`;
    card.append(title,temperature,humidity,time); root.append(card);
  }
  document.getElementById('status').textContent=data.readings.length ? `${data.readings.length} device(s) online` : 'No readings received yet';
}
refresh(); setInterval(refresh,3000);
</script></html>"""


def start_mqtt_listener(store: DeviceStore, host: str, port: int, topic: str):
    try:
        import paho.mqtt.client as mqtt
    except ImportError as error:
        raise RuntimeError("Install MQTT support with: pip install -r requirements.txt") from error

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    def on_connect(client, userdata, flags, reason_code, properties) -> None:
        if getattr(reason_code, "is_failure", False):
            LOGGER.error("MQTT connection failed: %s", reason_code)
            return
        client.subscribe(topic)
        LOGGER.info("Subscribed to %s", topic)

    def on_message(client, userdata, message) -> None:
        try:
            reading = store.update(message.payload)
            LOGGER.info("Updated reading from %s", reading["device_id"])
        except (UnicodeDecodeError, ValueError) as error:
            LOGGER.warning("Ignoring invalid message on %s: %s", message.topic, error)

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(host, port, keepalive=60)
    client.loop_start()
    return client


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve an MQTT sensor dashboard")
    parser.add_argument("--mqtt-host", help="Broker hostname; omit for dashboard-only mode")
    parser.add_argument("--mqtt-port", type=int, default=1883)
    parser.add_argument("--topic", default="sensors/+/telemetry")
    parser.add_argument("--web-host", default="127.0.0.1")
    parser.add_argument("--web-port", type=int, default=8080)
    parser.add_argument("--demo", action="store_true", help="Show clearly synthetic sample readings")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    store = DeviceStore()
    if args.demo:
        store.update({"device_id": "synthetic-demo-sensor", "temperature_c": 22.4, "humidity_pct": 48.0})
    mqtt_client = start_mqtt_listener(store, args.mqtt_host, args.mqtt_port, args.topic) if args.mqtt_host else None
    server = ThreadingHTTPServer((args.web_host, args.web_port), make_handler(store))
    print(f"Dashboard ready at http://{args.web_host}:{args.web_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        if mqtt_client:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()


if __name__ == "__main__":
    main()
