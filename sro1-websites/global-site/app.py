"""
Сайт №2 (глобальный): «Облачная доска».
Маленький веб-сервер только на стандартной библиотеке Python, без зависимостей.

  /            — страница
  /api/info    — где запущен сервер (хост, ОС, аптайм, данные AWS EC2)
  /api/notes   — гостевая книга: GET список, POST {"name": "...", "text": "..."}
  /health      — проверка для HEALTHCHECK
"""
import json
import os
import platform
import socket
import threading
import time
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", "8080"))
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
DATA_FILE = os.environ.get("NOTES_FILE", "/data/notes.json")
MAX_NOTES = 50

STARTED = time.time()
lock = threading.Lock()
visits = 0


def load_notes():
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def save_notes(notes):
    try:
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(notes, f, ensure_ascii=False)
    except OSError:
        pass  # без тома просто живём в памяти


notes = load_notes()


def ec2_metadata():
    """Если сервер на AWS EC2 — достаём instance-id, тип и зону через IMDSv2."""
    base = "http://169.254.169.254/latest"
    try:
        req = urllib.request.Request(
            base + "/api/token", method="PUT",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"},
        )
        token = urllib.request.urlopen(req, timeout=0.5).read().decode()
        result = {}
        for key, path in (("instance_id", "instance-id"),
                          ("instance_type", "instance-type"),
                          ("zone", "placement/availability-zone")):
            r = urllib.request.Request(base + "/meta-data/" + path,
                                       headers={"X-aws-ec2-metadata-token": token})
            result[key] = urllib.request.urlopen(r, timeout=0.5).read().decode()
        return result
    except Exception:
        return None


# Метаданные не меняются, спрашиваем один раз при старте
EC2 = ec2_metadata()


class Handler(SimpleHTTPRequestHandler):
    server_version = "CloudBoard/1.0"
    sys_version = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        global visits
        if self.path == "/health":
            return self.send_json({"status": "ok"})
        if self.path == "/api/info":
            return self.send_json({
                "hostname": socket.gethostname(),
                "os": f"{platform.system()} {platform.release()}",
                "arch": platform.machine(),
                "python": platform.python_version(),
                "uptime_sec": int(time.time() - STARTED),
                "visits": visits,
                "aws": EC2,
            })
        if self.path == "/api/notes":
            with lock:
                return self.send_json(list(reversed(notes)))
        if self.path in ("/", "/index.html"):
            with lock:
                visits += 1
        return super().do_GET()

    def do_POST(self):
        if self.path != "/api/notes":
            return self.send_json({"error": "not found"}, 404)
        try:
            length = min(int(self.headers.get("Content-Length", 0)), 2048)
            data = json.loads(self.rfile.read(length) or b"{}")
            name = str(data.get("name", "")).strip()[:30] or "Аноним"
            text = str(data.get("text", "")).strip()[:200]
        except (ValueError, AttributeError):
            return self.send_json({"error": "bad json"}, 400)
        if not text:
            return self.send_json({"error": "пустое сообщение"}, 400)
        with lock:
            notes.append({"name": name, "text": text, "time": int(time.time())})
            del notes[:-MAX_NOTES]
            save_notes(notes)
        return self.send_json({"ok": True}, 201)

    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {self.address_string()} {fmt % args}", flush=True)


if __name__ == "__main__":
    print(f"Cloud Board слушает порт {PORT}; AWS: {EC2 or 'нет'}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
