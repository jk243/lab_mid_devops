
import os
import json
import smtplib
from email.message import EmailMessage
from pathlib import Path

report_path = Path("test-report.json")
if not report_path.exists():
    raise SystemExit("test-report.json was not generated")

report = json.loads(report_path.read_text(encoding="utf-8"))

host = (os.getenv("SMTP_HOST") or "").strip()
port_value = (os.getenv("SMTP_PORT") or "587").strip()
username = (os.getenv("SMTP_USERNAME") or "").strip()
password = (os.getenv("SMTP_PASSWORD") or "").strip()
recipient = (os.getenv("REPORT_EMAIL_TO") or "").strip()

if not all([host, username, password, recipient]):
    raise SystemExit(
        "Email not sent: configure SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, "
        "and REPORT_EMAIL_TO in GitHub Actions Secrets"
    )

try:
    port = int(port_value)
except ValueError:
    raise SystemExit("SMTP_PORT must be a valid integer")
if not 1 <= port <= 65535:
    raise SystemExit("SMTP_PORT must be between 1 and 65535")

message = EmailMessage()
message["Subject"] = (
    f"CI {report['overall_status'].upper()}: "
    f"{report['repository']} @ {report['commit_sha'][:7]}"
)
message["From"] = username
message["To"] = recipient

message.set_content(
    f"Repository: {report['repository']}\n"
    f"Branch: {report['branch']}\n"
    f"Commit: {report['commit_sha']}\n"
    f"Run ID: {report['pipeline_run_id']}\n"
    f"Status: {report['overall_status']}\n"
    f"Total: {report['total']}\n"
    f"Passed: {report['passed']}\n"
    f"Failed: {report['failed']}\n\n"
    + "\n".join(
        f"{t['result']}: {t['name']}\n"
        f"Failure: {t['failure_message'] or 'None'}"
        for t in report["tests"]
    )
)

message.add_attachment(
    report_path.read_bytes(),
    maintype="application",
    subtype="json",
    filename="test-report.json"
)

if port == 465:
    smtp_connection = smtplib.SMTP_SSL(host, port, timeout=30)
else:
    smtp_connection = smtplib.SMTP(host, port, timeout=30)

try:
    with smtp_connection as server:
        server.ehlo()
        if port != 465:
            server.starttls()
            server.ehlo()
        server.login(username, password)
        server.send_message(message)
except (smtplib.SMTPException, OSError) as exc:
    security = "implicit SSL" if port == 465 else "STARTTLS"
    raise SystemExit(
        f"Email delivery failed via {host}:{port} ({security}): "
        f"{type(exc).__name__}: {exc}. Check SMTP secrets and server settings. "
        "For Gmail, use an App Password (not the normal account password)."
    ) from exc

print("Test report email sent successfully")
