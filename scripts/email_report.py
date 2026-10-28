
import os
import json
import smtplib
from email.message import EmailMessage
from pathlib import Path

report_path = Path("test-report.json")
if not report_path.exists():
    raise SystemExit("test-report.json was not generated")

report = json.loads(report_path.read_text(encoding="utf-8"))

host = os.getenv("SMTP_HOST")
port = int(os.getenv("SMTP_PORT", "587"))
username = os.getenv("SMTP_USERNAME")
password = os.getenv("SMTP_PASSWORD")
recipient = os.getenv("REPORT_EMAIL_TO")

if not all([host, username, password, recipient]):
    raise SystemExit("Configure SMTP GitHub Secrets before sending email")

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

with smtplib.SMTP(host, port) as server:
    server.starttls()
    server.login(username, password)
    server.send_message(message)

print("Test report email sent successfully")
