#!/usr/bin/env python3
"""Lightweight email sending service (stdlib only)."""
import os
import json
import logging
import smtplib
import ssl
import re
from html import escape
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


def send_email(to, subject, content, html=False, plain_content=None):
    msg = MIMEMultipart("alternative")
    msg["From"] = SENDER
    msg["To"] = to
    msg["Subject"] = subject
    if html:
        msg.attach(MIMEText(plain_content or "", "plain", "utf-8"))
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


def list_value(data, *names):
    for name in names:
        value = data.get(name)
        if value is not None:
            if isinstance(value, list):
                return [str(item).strip() for item in value if str(item).strip()]
            value = str(value).strip()
            return [value] if value else []
    return []


def appointment_details(data):
    """Validate and normalize the legacy appointment form."""
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

    return {
        "form_type": "appointment",
        "name": name,
        "company": company,
        "phone": phone,
        "recipient": recipient,
        "company_type": company_type or "未填写",
        "requirement": requirement or "未填写",
    }


def trial_application_details(data):
    """Validate and normalize the current nuVision trial form."""
    required_fields = (
        ("name", "name"),
        ("phone", "phone"),
        ("operatingSystem", "operatingSystem"),
        ("dataSize", "dataSize"),
        ("deployment", "deployment"),
        ("loadTime", "loadTime"),
        ("concurrencySupport", "concurrencySupport"),
        ("usedAccelerator", "usedAccelerator"),
        ("expectedLoadTime", "expectedLoadTime"),
        ("expectedConcurrency", "expectedConcurrency"),
    )
    fields = {key: first_value(data, key) for key, _ in required_fields}
    fields["dataTypes"] = list_value(data, "dataTypes")
    fields["acceptableDeployment"] = list_value(data, "acceptableDeployment")
    fields.update({
        "operatingSystemOther": first_value(data, "operatingSystemOther"),
        "deploymentOther": first_value(data, "deploymentOther"),
        "dataTypesOther": first_value(data, "dataTypesOther"),
        "acceptableDeploymentOther": first_value(data, "acceptableDeploymentOther"),
        "departmentPosition": first_value(data, "departmentPosition"),
        "organizationType": first_value(data, "organizationType"),
        "industry": first_value(data, "industry"),
        "industryOther": first_value(data, "industryOther"),
        "systemUses": list_value(data, "systemUses"),
        "systemUsesOther": first_value(data, "systemUsesOther"),
        "recipient": first_value(data, "email", "to", "recipient") or DEFAULT_RECIPIENT,
    })

    missing = [key for key, _ in required_fields if not fields[key]]
    if not fields["dataTypes"]:
        missing.append("dataTypes")
    if not fields["acceptableDeployment"]:
        missing.append("acceptableDeployment")
    if missing:
        raise ValueError("missing required fields: " + ", ".join(missing))
    if fields["operatingSystem"] == "其它" and not fields["operatingSystemOther"]:
        raise ValueError("operatingSystemOther is required when operatingSystem is 其它")
    if fields["deployment"] == "其它" and not fields["deploymentOther"]:
        raise ValueError("deploymentOther is required when deployment is 其它")
    if "其它" in fields["dataTypes"] and not fields["dataTypesOther"]:
        raise ValueError("dataTypesOther is required when dataTypes includes 其它")
    if "其它" in fields["acceptableDeployment"] and not fields["acceptableDeploymentOther"]:
        raise ValueError("acceptableDeploymentOther is required when acceptableDeployment includes 其它")
    if data.get("privacyAccepted") is not True:
        raise ValueError("privacyAccepted must be true")
    if not EMAIL_PATTERN.fullmatch(fields["recipient"]):
        raise ValueError("email must be a valid email address")
    if any(len(str(value)) > 5000 for value in fields.values() if isinstance(value, str)):
        raise ValueError("form field is too long")
    return fields


def html_row(label, value):
    if isinstance(value, list):
        value = "、".join(value) if value else "未填写"
    return (
        '<tr><td style="padding:12px 14px;border-bottom:1px solid #e8edf3;'
        'color:#718096;width:180px;vertical-align:top;">'
        f"{escape(label)}</td><td style=\"padding:12px 14px;border-bottom:1px solid #e8edf3;"
        f'color:#1f2937;font-weight:600;">{escape(str(value or "未填写"))}</td></tr>'
    )


def build_trial_application(data):
    fields = trial_application_details(data)
    labels = (
        ("基础信息", (
            ("您的称呼", "name"), ("联系电话", "phone"),
        )),
        ("现有系统基础信息", (
            ("系统运行操作系统", "operatingSystem"),
            ("操作系统补充说明", "operatingSystemOther"),
            ("系统数据大小", "dataSize"),
            ("系统现有部署方式", "deployment"),
            ("部署方式补充说明", "deploymentOther"),
            ("系统目前加载时间", "loadTime"),
            ("系统数据类型", "dataTypes"),
            ("数据类型补充说明", "dataTypesOther"),
            ("系统是否支持多用户并发", "concurrencySupport"),
            ("是否试用过其它加速软件", "usedAccelerator"),
        )),
        ("加速功能需求", (
            ("期望的系统加载速度", "expectedLoadTime"),
            ("期望的并发数量", "expectedConcurrency"),
            ("可接受的部署方式", "acceptableDeployment"),
            ("部署方式补充说明", "acceptableDeploymentOther"),
        )),
        ("辅助筛选信息", (
            ("部门与职位", "departmentPosition"),
            ("单位性质", "organizationType"),
            ("系统所属行业", "industry"),
            ("行业补充说明", "industryOther"),
            ("系统主要用途", "systemUses"),
            ("用途补充说明", "systemUsesOther"),
        )),
    )
    plain_sections = []
    html_sections = []
    for section, section_fields in labels:
        plain_sections.append(section)
        rows = []
        for label, key in section_fields:
            value = fields[key]
            if value:
                plain_sections.append(f"{label}：{', '.join(value) if isinstance(value, list) else value}")
                rows.append(html_row(label, value))
        html_sections.append(
            f'<div style="margin-top:24px;font-size:16px;font-weight:700;color:#10213d;">{section}</div>'
            f'<table role="presentation" cellpadding="0" cellspacing="0" width="100%" '
            'style="margin-top:10px;border:1px solid #e8edf3;border-radius:8px;'
            'border-collapse:separate;border-spacing:0;overflow:hidden;">'
            + "".join(rows) + "</table>"
        )
    plain = "nuVision 产品试用申请\n" + "=" * 28 + "\n" + "\n".join(plain_sections)
    html = f"""<!doctype html>
<html lang="zh-CN"><body style="margin:0;padding:0;background:#f3f6fa;font-family:Arial,'Microsoft YaHei',sans-serif;color:#1f2937;">
  <div style="max-width:720px;margin:0 auto;padding:32px 16px;">
    <div style="background:#10213d;border-radius:12px 12px 0 0;padding:26px 32px;">
      <div style="font-size:13px;letter-spacing:2px;color:#8ec5ff;">PRODUCT TRIAL</div>
      <div style="margin-top:8px;font-size:24px;line-height:1.4;font-weight:700;color:#ffffff;">nuVision 产品试用申请</div>
      <div style="margin-top:6px;font-size:13px;color:#b8c7dc;">收到一条新的产品试用申请，请及时跟进</div>
    </div>
    <div style="background:#ffffff;border:1px solid #e4eaf1;border-top:0;border-radius:0 0 12px 12px;padding:8px 32px 28px;">
      {''.join(html_sections)}
      <div style="margin-top:26px;padding-top:16px;border-top:1px solid #edf1f5;font-size:12px;line-height:1.7;color:#9aa6b5;">此邮件由栖云科技官网 nuVision 试用申请表单自动发送。</div>
    </div>
  </div>
</body></html>"""
    return fields["recipient"], f"nuVision 产品试用申请 - {fields['name']}", plain, html


def build_appointment(data):
    """Build the plain-text fallback and HTML email for the demo form."""
    fields = appointment_details(data)
    content = "\n".join((
        "预约产品演示表单",
        "=" * 24,
        f"姓名：{fields['name']}",
        f"单位名称：{fields['company']}",
        f"手机号：{fields['phone']}",
        f"邮箱：{fields['recipient']}",
        f"单位类型：{fields['company_type']}",
        f"需求简述：{fields['requirement']}",
    ))
    table_rows = "".join(
        f'<tr><td style="padding:13px 16px;border-bottom:1px solid #e8edf3;'
        f'color:#718096;width:92px;vertical-align:top;">{label}</td>'
        f'<td style="padding:13px 16px;border-bottom:1px solid #e8edf3;'
        f'color:#1f2937;font-weight:600;">{escape(value)}</td></tr>'
        for label, value in (
            ("姓名", fields["name"]),
            ("单位名称", fields["company"]),
            ("手机号", fields["phone"]),
            ("联系邮箱", fields["recipient"]),
            ("单位类型", fields["company_type"]),
        )
    )
    html_content = f"""<!doctype html>
<html lang="zh-CN"><body style="margin:0;padding:0;background:#f3f6fa;font-family:Arial,'Microsoft YaHei',sans-serif;color:#1f2937;">
  <div style="max-width:680px;margin:0 auto;padding:32px 16px;">
    <div style="background:#10213d;border-radius:12px 12px 0 0;padding:26px 32px;">
      <div style="font-size:13px;letter-spacing:2px;color:#8ec5ff;">Qiyun Technology</div>
      <div style="margin-top:8px;font-size:24px;line-height:1.4;font-weight:700;color:#ffffff;">预约产品演示</div>
      <div style="margin-top:6px;font-size:13px;color:#b8c7dc;">收到一条新的产品演示预约申请</div>
    </div>
    <div style="background:#ffffff;border:1px solid #e4eaf1;border-top:0;border-radius:0 0 12px 12px;padding:28px 32px;">
      <div style="font-size:16px;font-weight:700;color:#10213d;margin-bottom:14px;">联系人信息</div>
      <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border:1px solid #e8edf3;border-radius:8px;border-collapse:separate;border-spacing:0;overflow:hidden;">
        {table_rows}
      </table>
      <div style="margin-top:26px;font-size:16px;font-weight:700;color:#10213d;">需求简述</div>
      <div style="margin-top:12px;padding:16px;background:#f7f9fc;border-left:4px solid #ff704d;border-radius:4px;color:#4a5568;line-height:1.75;white-space:pre-wrap;">{escape(fields['requirement'])}</div>
      <div style="margin-top:26px;padding-top:16px;border-top:1px solid #edf1f5;font-size:12px;line-height:1.7;color:#9aa6b5;">此邮件由栖云科技官网预约表单自动发送，请及时联系客户。</div>
    </div>
  </div>
</body></html>"""
    return fields["recipient"], f"预约产品演示 - {fields['name']} - {fields['company']}", content, html_content


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
        if path in ("/appointment", "/api/appointment") and "operatingSystem" in data:
            try:
                to, subject, content, html_content = build_trial_application(data)
            except ValueError as e:
                self._send_json(400, {"error": str(e)})
                return
            html = True
            email_content = html_content
        elif path in ("/appointment", "/api/appointment"):
            try:
                to, subject, content, html_content = build_appointment(data)
            except ValueError as e:
                self._send_json(400, {"error": str(e)})
                return
            html = True
            email_content = html_content
        else:
            subject = str(data.get("subject", "")).strip()
            content = data.get("content", "")
            html = bool(data.get("html", False))
            to = str(data.get("to", DEFAULT_RECIPIENT)).strip()
            email_content = content
        if not subject or not content or not to:
            self._send_json(400, {"error": "subject, content and to are required"})
            return
        if len(to) > 4096 or len(subject) > 1024 or len(content) > 1024 * 1024:
            self._send_json(400, {"error": "payload too large"})
            return
        try:
            send_email(to, subject, email_content, html, content)
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
