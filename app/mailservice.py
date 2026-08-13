#!/usr/bin/env python3
"""Lightweight email sending service (stdlib only)."""
import os
import json
import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HOST = os.environ.get("MAIL_SERVICE_HOST", "0.0.0.0")
PORT = int(os.environ.get("MAIL_SERVICE_PORT", "8080"))
SMTP_HOST = os.environ.get("MAIL_SMTP_HOST", "smtp.163.com")
SMTP_PORT = int(os.environ.get("MAIL_SMTP_PORT", "465"))
SENDER = os.environ.get("MAIL_SENDER", "")
AUTH_CODE = os.environ.get("MAIL_AUTH_CODE", "")
DEFAULT_RECIPIENT = os.environ.get("MAIL_RECIPIENT", "")
API_KEYS = set(k.strip() for k in os.environ.get("MAIL_API_KEYS", "").split(",") if k.strip())

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("mailservice")


def send_email(to, subject, content, html=False):
    msg = MIMEMultipart("alternative")
    msg["From"] = SENDER
    msg["To"] = to
    msg["Subject"] = subject
    if html:
        msg.attach(MIMEText(content, "html", "utf-8"))
    else:
        msg.attach(MIMEText(content, "plain", "utf-8"))
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=30) as server:
        server.login(SENDER, AUTH_CODE)
        server.sendmail(SENDER, [to], msg.as_string())
    return True


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/health", "/healthz"):
            self._send_json(200, {"status": "ok", "service": "mail-service"})
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/send":
            self._send_json(404, {"error": "not found"})
            return
        if API_KEYS:
            key = self.headers.get("X-API-Key", "")
            if key not in API_KEYS:
                self._send_json(401, {"error": "unauthorized"})
                return
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0 or length > 1024 * 1024:
            self._send_json(400, {"error": "invalid body size"})
            return
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            self._send_json(400, {"error": "invalid json"})
            return
        subject = str(data.get("subject", "")).strip()
        content = data.get("content", "")
        html = bool(data.get("html", False))
        to = str(data.get("to", DEFAULT_RECIPIENT)).strip()
        if not subject or not content or not to:
            self._send_json(400, {"error": "subject, content and to are required"})
            return
        if len(to) > 4096 or len(subject) > 1024 or len(content) > 1024 * 1024:
            self._send_json(400, {"error": "payload too large"})
            return
        try:
            send_email(to, subject, content, html)
            log.info("email sent to %s subject=%r", to, subject[:80])
            self._send_json(200, {"status": "sent", "to": to})
        except Exception as e:
            log.exception("send failed")
            self._send_json(502, {"error": "send failed", "detail": str(e)})

    def log_message(self, fmt, *args):
        log.info("%s - %s", self.address_string(), fmt % args)


if __name__ == "__main__":
    if not SENDER or not AUTH_CODE or not DEFAULT_RECIPIENT:
        log.error("Missing required env vars (MAIL_SENDER, MAIL_AUTH_CODE, MAIL_RECIPIENT)")
        raise SystemExit(1)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    log.info("mail service listening on %s:%s (sender=%s)", HOST, PORT, SENDER)
    server.serve_forever()
