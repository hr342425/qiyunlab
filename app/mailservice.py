#!/usr/bin/env python3
"""Lightweight email sending service (stdlib only)."""
import os
import json
import logging
import smtplib
import ssl
import re
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
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


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


def first_value(data, *names):
    for name in names:
        value = data.get(name)
        if value is not None:
            return str(value).strip()
    return ""


def build_appointment(data):
    """Validate the demo request form and turn it into an email payload."""
    name = first_value(data, "name", "姓名")
    company = first_value(data, "company", "companyName", "unitName", "单位名称")
    phone = first_value(data, "phone", "mobile", "手机号")
    recipient = first_value(data, "email", "to", "recipient", "邮箱") or DEFAULT_RECIPIENT
    company_type = first_value(data, "companyType", "unitType", "type", "单位类型")
    requirement = first_value(data, "requirement", "description", "demand", "需求简述")

    missing = [label for value, label in (
        (name, "name"), (company, "company"), (phone, "phone")
    ) if not value]
    if missing:
        raise ValueError("missing required fields: " + ", ".join(missing))
    if not EMAIL_PATTERN.fullmatch(recipient):
        raise ValueError("email must be a valid email address")
    if len(name) > 100 or len(company) > 200 or len(phone) > 40:
        raise ValueError("name, company or phone is too long")
    if len(company_type) > 100 or len(requirement) > 5000:
        raise ValueError("companyType or requirement is too long")

    content = "\n".join((
        "预约产品演示表单",
        "=" * 24,
        f"姓名：{name}",
        f"单位名称：{company}",
        f"手机号：{phone}",
        f"邮箱：{recipient}",
        f"单位类型：{company_type or '未填写'}",
        f"需求简述：{requirement or '未填写'}",
    ))
    return recipient, f"预约产品演示 - {name} - {company}", content


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-API-Key")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
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
        if path not in ("/send", "/appointment", "/api/appointment"):
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
        if path in ("/appointment", "/api/appointment"):
            try:
                to, subject, content = build_appointment(data)
            except ValueError as e:
                self._send_json(400, {"error": str(e)})
                return
            html = False
        else:
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

    def do_OPTIONS(self):
        self._send_json(204, {})

    def log_message(self, fmt, *args):
        log.info("%s - %s", self.address_string(), fmt % args)


if __name__ == "__main__":
    if not SENDER or not AUTH_CODE or not DEFAULT_RECIPIENT:
        log.error("Missing required env vars (MAIL_SENDER, MAIL_AUTH_CODE, MAIL_RECIPIENT)")
        raise SystemExit(1)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    log.info("mail service listening on %s:%s (sender=%s)", HOST, PORT, SENDER)
    server.serve_forever()
