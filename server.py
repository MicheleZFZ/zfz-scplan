#!/usr/bin/env python3
"""
科研计划板 — Server for Render.com deployment
==============================================
Deploy on Render.com (free tier):
  1. Push this folder to GitHub
  2. Create new Web Service on Render → connect repo
  3. Set: Start Command = "python3 server.py"
  4. Deploy → get URL like https://zfz-scplan.onrender.com

API endpoints:
  GET  / → 计划板网页
  GET  /api/plan → 获取计划 JSON
  POST /api/plan → 保存计划 JSON
  GET  /api/history → 获取历史记录
"""
import json
import os
import http.server
import urllib.parse
from datetime import date

# Render provides PORT env var
PORT = int(os.environ.get("PORT", 8080))
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

TOMORROW_FILE = os.path.join(DATA_DIR, "tomorrow.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")


def ensure_defaults():
    if not os.path.exists(TOMORROW_FILE):
        with open(TOMORROW_FILE, "w") as f:
            json.dump({"date": "", "items": [], "note": ""}, f)
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w") as f:
            json.dump([], f)


def load_plan():
    ensure_defaults()
    with open(TOMORROW_FILE) as f:
        return json.load(f)


def save_plan(plan):
    ensure_defaults()
    with open(TOMORROW_FILE, "w") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    # Also save to history
    history = load_history()
    history.append({
        "date": str(date.today()),
        "plan_date": plan.get("date", ""),
        "items": plan.get("items", []),
    })
    with open(HISTORY_FILE, "w") as f:
        json.dump(history[-30:], f, ensure_ascii=False, indent=2)


def load_history():
    ensure_defaults()
    with open(HISTORY_FILE) as f:
        return json.load(f)


def load_html():
    path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    # Fallback inline HTML
    return """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>计划板</title></head>
<body><h1>📋 科研计划板</h1><p>正在加载...</p></body></html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/plan":
            self._json(load_plan())
        elif parsed.path == "/api/history":
            self._json(load_history())
        elif parsed.path == "/":
            self._html(load_html())
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/plan":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            plan = json.loads(body)
            save_plan(plan)
            self._json({"status": "ok"})
        else:
            self.send_error(404)

    def _json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, fmt, *args):
        print(f"[PlanServer] {args[0]}")


if __name__ == "__main__":
    ensure_defaults()
    print(f"🌐 科研计划板启动! http://0.0.0.0:{PORT}")
    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
