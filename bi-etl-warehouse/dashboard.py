import argparse
import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from etl import summarize


def render_dashboard(database_path: str | Path) -> str:
    summary = summarize(database_path)
    region_rows = "".join(
        "<tr><td>{}</td><td>{:,.2f}</td><td>{}</td></tr>".format(
            html.escape(row["region"]), row["revenue"], row["units"]
        )
        for row in summary["by_region"]
    )
    return f"""<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sales Warehouse</title>
<style>
body{{font:16px system-ui,sans-serif;max-width:920px;margin:40px auto;padding:0 20px;color:#17202a;background:#f4f7f8}}
h1{{font-size:2rem}}.metrics{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}}
.metric,table{{background:white;border:1px solid #dce4e8;border-radius:8px;padding:18px}}
.metric strong{{display:block;font-size:1.5rem;margin-top:8px}}table{{width:100%;border-collapse:collapse;margin-top:18px;padding:0}}
th,td{{text-align:left;padding:12px;border-bottom:1px solid #e7ecef}}th{{color:#52616b}}
</style>
<h1>Sales Warehouse</h1>
<p>Locally generated summary from the SQLite star schema.</p>
<section class="metrics">
<div class="metric">Sales<strong>{summary['sale_count']}</strong></div>
<div class="metric">Revenue<strong>{summary['revenue']:,.2f}</strong></div>
<div class="metric">Average sale<strong>{summary['average_sale']:,.2f}</strong></div>
</section>
<table><thead><tr><th>Region</th><th>Revenue</th><th>Units</th></tr></thead><tbody>{region_rows}</tbody></table>
"""


def make_handler(database_path: str):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/api/summary":
                body = json.dumps(summarize(database_path)).encode("utf-8")
                content_type = "application/json; charset=utf-8"
            elif self.path == "/":
                body = render_dashboard(database_path).encode("utf-8")
                content_type = "text/html; charset=utf-8"
            else:
                body = b"Not found"
                self.send_response(404)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the local sales warehouse dashboard")
    parser.add_argument("--db", default="warehouse.db")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    database_path = str(Path(args.db).expanduser())
    with ThreadingHTTPServer((args.host, args.port), make_handler(database_path)) as server:
        print(f"Dashboard ready at http://{args.host}:{args.port}")
        server.serve_forever()


if __name__ == "__main__":
    main()
