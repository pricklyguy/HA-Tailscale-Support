#!/usr/bin/env python3
"""Prickly Guy Remote Support - Home Assistant App v2.

Small dependency-free web UI and Tailscale API client. The app keeps the
short-lived Tailscale access token in memory and persists only session state.
"""

from __future__ import annotations

import html
import json
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DATA_DIR = Path("/data")
OPTIONS_FILE = DATA_DIR / "options.json"
STATE_FILE = DATA_DIR / "state.json"
HOST = "0.0.0.0"
PORT = 8099
INGRESS_PROXY = "172.30.32.2"
TOKEN_URL = "https://api.tailscale.com/api/v2/oauth/token"
API_BASE = "https://api.tailscale.com/api/v2"


def load_json(path: Path, default: dict) -> dict:
    try:
        with path.open("r", encoding="utf-8") as f:
            value = json.load(f)
            return value if isinstance(value, dict) else default.copy()
    except (OSError, ValueError):
        return default.copy()


def save_json(path: Path, value: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as f:
        json.dump(value, f, indent=2)
    os.replace(temp, path)


OPTIONS = load_json(OPTIONS_FILE, {})
STATE = load_json(
    STATE_FILE,
    {
        "active": False,
        "started_at": None,
        "expires_at": None,
        "original_tags": None,
        "last_error": None,
    },
)
LOCK = threading.RLock()
TOKEN = None
TOKEN_EXPIRES_AT = 0.0


def option(name: str, default: str = "") -> str:
    value = OPTIONS.get(name, default)
    return str(value) if value is not None else default


def timeout_minutes() -> int:
    try:
        return max(30, min(480, int(OPTIONS.get("default_timeout_minutes", 120))))
    except (TypeError, ValueError):
        return 120


def configured() -> bool:
    return all(
        [
            option("tailscale_client_id"),
            option("tailscale_client_secret"),
            option("tailscale_device_id"),
        ]
    )


def request(url: str, method: str = "GET", data: bytes | None = None, headers=None) -> tuple[int, bytes]:
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def get_token(force: bool = False) -> str:
    global TOKEN, TOKEN_EXPIRES_AT
    with LOCK:
        if not force and TOKEN and time.time() < TOKEN_EXPIRES_AT - 120:
            return TOKEN

        client_id = option("tailscale_client_id")
        client_secret = option("tailscale_client_secret")
        body = urllib.parse.urlencode(
            {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "devices:core",
            }
        ).encode()
        status, raw = request(
            TOKEN_URL,
            method="POST",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if status >= 400:
            raise RuntimeError(f"Tailscale token request failed ({status}): {raw.decode(errors='replace')[:300]}")
        payload = json.loads(raw)
        TOKEN = payload["access_token"]
        TOKEN_EXPIRES_AT = time.time() + int(payload.get("expires_in", 3600))
        return TOKEN


def tailscale(method: str, path: str, payload: dict | None = None, retry=True) -> dict:
    token = get_token()
    body = json.dumps(payload).encode() if payload is not None else None
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    status, raw = request(API_BASE + path, method=method, data=body, headers=headers)
    if status == 401 and retry:
        get_token(force=True)
        return tailscale(method, path, payload, retry=False)
    if status >= 400:
        raise RuntimeError(f"Tailscale API returned {status}: {raw.decode(errors='replace')[:400]}")
    if not raw:
        return {}
    return json.loads(raw)


def get_device() -> dict:
    return tailscale("GET", f"/device/{urllib.parse.quote(option('tailscale_device_id'), safe='')}")


def set_tags(tags: list[str]) -> None:
    device_id = urllib.parse.quote(option("tailscale_device_id"), safe="")
    tailscale("POST", f"/device/{device_id}/tags", {"tags": tags})


def enable() -> None:
    with LOCK:
        if not configured():
            raise RuntimeError("The Tailscale credentials and device ID have not been configured.")
        device = get_device()
        current_tags = device.get("tags") or []
        support_tag = option("support_tag", "tag:support-enabled")
        client_tag = option("client_tag", "tag:client-device")
        original_tags = current_tags.copy()
        if support_tag not in original_tags:
            set_tags([support_tag])
        now = time.time()
        STATE.update(
            active=True,
            started_at=now,
            expires_at=now + timeout_minutes() * 60,
            original_tags=original_tags or [client_tag],
            last_error=None,
        )
        save_json(STATE_FILE, STATE)


def disable(reason: str = "manual") -> None:
    with LOCK:
        if not configured():
            STATE.update(active=False, started_at=None, expires_at=None)
            save_json(STATE_FILE, STATE)
            return
        original = STATE.get("original_tags") or [option("client_tag", "tag:client-device")]
        set_tags(original)
        STATE.update(active=False, started_at=None, expires_at=None, original_tags=None, last_error=None)
        save_json(STATE_FILE, STATE)


def remaining_seconds() -> int:
    with LOCK:
        if not STATE.get("active") or not STATE.get("expires_at"):
            return 0
        return max(0, int(STATE["expires_at"] - time.time()))


def timeout_worker() -> None:
    while True:
        time.sleep(2)
        try:
            with LOCK:
                expired = STATE.get("active") and remaining_seconds() <= 0
            if expired:
                disable("timeout")
        except Exception as exc:  # Keep the watchdog alive; expose the error in UI/logs.
            with LOCK:
                STATE["last_error"] = str(exc)
                save_json(STATE_FILE, STATE)
            print(f"[ERROR] Automatic support shutdown failed: {exc}", flush=True)


def fmt_remaining(seconds: int) -> str:
    if seconds <= 0:
        return "Expired"
    minutes = (seconds + 59) // 60
    hours, mins = divmod(minutes, 60)
    return f"{hours}h {mins:02d}m" if hours else f"{mins} min"


def page(message: str = "") -> bytes:
    active = bool(STATE.get("active"))
    remaining = remaining_seconds()
    status_text = "SUPPORT ACCESS ACTIVE" if active else "SYSTEM SECURE"
    status_class = "active" if active else "secure"
    button_label = "End Support Session" if active else "Enable Remote Support"
    button_action = "/disable" if active else "/enable"
    message_html = f'<div class="message">{html.escape(message)}</div>' if message else ""
    device_text = option("tailscale_device_id") or "Not configured"
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Prickly Guy Remote Support</title>
<style>
body{{font-family:system-ui,-apple-system,sans-serif;background:#111827;color:#f9fafb;margin:0;padding:24px}}
main{{max-width:650px;margin:auto}} h1{{font-size:1.8rem}} .card{{background:#1f2937;border-radius:18px;padding:24px;margin-top:18px;box-shadow:0 8px 30px #0004}}
.status{{border-radius:14px;padding:20px;text-align:center;font-weight:800;letter-spacing:.05em}} .secure{{background:#064e3b}} .active{{background:#78350f}}
.big{{font-size:2rem;margin:8px 0}} .muted{{color:#9ca3af}} button{{width:100%;padding:16px;border:0;border-radius:12px;font-size:1.05rem;font-weight:700;cursor:pointer;background:#f59e0b;color:#111827}}
.active + .card button{{background:#ef4444;color:white}} .message{{background:#374151;padding:12px;border-radius:10px;margin-top:15px;white-space:pre-wrap}}
code{{word-break:break-all}} a{{color:#93c5fd}}
</style></head><body><main>
<h1>🛠️ Prickly Guy Remote Support</h1>
<p class="muted">Client-controlled Tailscale access for Home Assistant.</p>
<div class="status {status_class}">{status_text}<div class="big">{fmt_remaining(remaining) if active else 'Remote access is off'}</div></div>
<div class="card">
<form method="post" action="{button_action}"><button type="submit">{button_label}</button></form>
<p class="muted">Support access automatically ends after the configured timeout. You can end it at any time.</p>
</div>
<div class="card"><b>Device</b><p><code>{html.escape(device_text)}</code></p>
<p class="muted">Support tag: <code>{html.escape(option('support_tag','tag:support-enabled'))}</code><br>Client tag: <code>{html.escape(option('client_tag','tag:client-device'))}</code></p></div>
{message_html}
</main></body></html>""".encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[HTTP] {self.address_string()} - {fmt % args}", flush=True)

    def allowed(self) -> bool:
        # Home Assistant Ingress proxies requests from this address. Reject direct access.
        return self.client_address[0] == INGRESS_PROXY

    def send_page(self, message="", status=200):
        body = page(message)
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.allowed():
            self.send_error(403, "Ingress access only")
            return
        if self.path in ("/", ""):
            self.send_page()
        elif self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_error(404)

    def do_POST(self):
        if not self.allowed():
            self.send_error(403, "Ingress access only")
            return
        try:
            if self.path == "/enable":
                enable()
                self.send_page("Remote support is now enabled.")
            elif self.path == "/disable":
                disable()
                self.send_page("Remote support has been disabled.")
            else:
                self.send_error(404)
        except Exception as exc:
            with LOCK:
                STATE["last_error"] = str(exc)
                save_json(STATE_FILE, STATE)
            print(f"[ERROR] {exc}", flush=True)
            self.send_page(f"Operation failed: {exc}", 500)


def startup_recovery() -> None:
    if STATE.get("active") and remaining_seconds() <= 0:
        try:
            disable("startup-expired")
        except Exception as exc:
            print(f"[ERROR] Could not restore client tags after startup: {exc}", flush=True)


if __name__ == "__main__":
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    startup_recovery()
    threading.Thread(target=timeout_worker, daemon=True).start()
    print(f"Prickly Guy Remote Support listening on {HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
