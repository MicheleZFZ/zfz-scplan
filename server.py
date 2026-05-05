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
  GET  /api/plan → 获取明日计划 JSON
  POST /api/plan → 保存明日计划 JSON
  GET  /api/monthly-plan → 获取本月计划 JSON
  POST /api/monthly-plan → 保存本月计划 JSON
  GET  /api/yearly-plan → 获取本年计划 JSON
  POST /api/yearly-plan → 保存本年计划 JSON
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
MONTHLY_FILE = os.path.join(DATA_DIR, "monthly.json")
YEARLY_FILE = os.path.join(DATA_DIR, "yearly.json")

EMPTY_PLAN = {"date": "", "items": [], "note": ""}


def ensure_defaults():
    if not os.path.exists(TOMORROW_FILE):
        with open(TOMORROW_FILE, "w") as f:
            json.dump(EMPTY_PLAN, f)
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w") as f:
            json.dump([], f)
    if not os.path.exists(MONTHLY_FILE):
        with open(MONTHLY_FILE, "w") as f:
            json.dump({"items": []}, f)
    if not os.path.exists(YEARLY_FILE):
        with open(YEARLY_FILE, "w") as f:
            json.dump({"items": []}, f)


# ─── Daily Plan ─────────────────────────────────────────────


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


# ─── Monthly Plan ────────────────────────────────────────────


def load_monthly():
    ensure_defaults()
    with open(MONTHLY_FILE) as f:
        return json.load(f)


def save_monthly(data):
    ensure_defaults()
    with open(MONTHLY_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ─── Yearly Plan ─────────────────────────────────────────────


def load_yearly():
    ensure_defaults()
    with open(YEARLY_FILE) as f:
        return json.load(f)


def save_yearly(data):
    ensure_defaults()
    with open(YEARLY_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ─── History ─────────────────────────────────────────────────


def load_history():
    ensure_defaults()
    with open(HISTORY_FILE) as f:
        return json.load(f)


# ─── HTML ────────────────────────────────────────────────────


def load_html():
    path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    # Fallback inline HTML
    return """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>计划板</title></head>
<body><h1>📋 科研计划板</h1><p>正在加载...</p></body></html>"""


# ─── HTTP Handler ────────────────────────────────────────────


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path == "/api/plan":
            self._json(load_plan())
        elif path == "/api/monthly-plan":
            self._json(load_monthly())
        elif path == "/api/yearly-plan":
            self._json(load_yearly())
        elif path == "/api/history":
            self._json(load_history())
        elif path == "/api/health":
            self._json({"status": "ok", "version": "v2"})
        elif path == "" or path == "/":
            self._html(load_html())
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        data = json.loads(body)

        if path == "/api/plan":
            save_plan(data)
            self._json({"status": "ok"})
        elif path == "/api/monthly-plan":
            save_monthly(data)
            self._json({"status": "ok"})
        elif path == "/api/yearly-plan":
            save_yearly(data)
            self._json({"status": "ok"})
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

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
    print(f"🌐 科研计划板 v2 启动! http://0.0.0.0:{PORT}")
    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
