import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.request import urlopen

from mqtt_dashboard import DeviceStore, make_handler


class DeviceStoreTests(unittest.TestCase):
    def test_valid_sensor_readings_are_stored_by_device(self) -> None:
        store = DeviceStore()
        store.update(json.dumps({"device_id": "sensor-2", "temperature_c": 21.5, "humidity_pct": 45}))
        store.update({"device_id": "sensor-1", "temperature_c": 19, "humidity_pct": 51})
        latest = store.latest()
        self.assertEqual([item["device_id"] for item in latest], ["sensor-1", "sensor-2"])
        self.assertEqual(latest[1]["temperature_c"], 21.5)

    def test_rejects_out_of_range_reading(self) -> None:
        store = DeviceStore()
        with self.assertRaisesRegex(ValueError, "humidity_pct"):
            store.update({"device_id": "sensor-1", "temperature_c": 20, "humidity_pct": 110})

    def test_http_api_returns_latest_readings(self) -> None:
        store = DeviceStore()
        store.update({"device_id": "sensor-1", "temperature_c": 20, "humidity_pct": 40})
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(store))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with urlopen(f"http://127.0.0.1:{server.server_port}/api/latest") as response:
                payload = json.loads(response.read().decode("utf-8"))
            self.assertEqual(payload["readings"][0]["device_id"], "sensor-1")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
