#!/usr/bin/env python3
"""Send an email notification via SMTP.

Uses only Python stdlib (smtplib + email.mime). No pip install needed.
Output: JSON to stdout.
"""

import argparse
import json
import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any


def send_email(
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    from_addr: str,
    to_addr: str,
    subject: str,
    body: str,
) -> dict[str, Any]:
    """Send a plain-text email via SMTP with STARTTLS."""
    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_password)
            server.sendmail(from_addr, [to_addr], msg.as_string())
        return {"status": "sent"}
    except smtplib.SMTPAuthenticationError as exc:
        return {"status": "failed", "error": f"SMTP auth failed: {exc}"}
    except smtplib.SMTPException as exc:
        return {"status": "failed", "error": f"SMTP error: {exc}"}
    except OSError as exc:
        return {"status": "failed", "error": f"Connection error: {exc}"}
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Send email notification via SMTP.")
    p.add_argument("--smtp-host", required=True, help="SMTP server hostname.")
    p.add_argument("--smtp-port", type=int, default=587, help="SMTP port (default: 587).")
    p.add_argument("--smtp-user", required=True, help="SMTP login username.")
    p.add_argument("--smtp-password", required=True, help="SMTP login password.")
    p.add_argument("--from", dest="from_addr", required=True, help="Sender email address.")
    p.add_argument("--to", required=True, help="Recipient email address.")
    p.add_argument("--subject", required=True, help="Email subject line.")
    p.add_argument("--body", required=True, help="Email body text.")
    return p


def main() -> None:
    args = build_parser().parse_args()

    result = send_email(
        smtp_host=args.smtp_host,
        smtp_port=args.smtp_port,
        smtp_user=args.smtp_user,
        smtp_password=args.smtp_password,
        from_addr=args.from_addr,
        to_addr=args.to,
        subject=args.subject,
        body=args.body,
    )
    print(json.dumps(result, ensure_ascii=False))

    if result["status"] == "failed":
        sys.exit(1)


if __name__ == "__main__":
    main()
