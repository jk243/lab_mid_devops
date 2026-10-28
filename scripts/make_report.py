
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

raw_path = Path("raw-test-report.json")
report_path = Path("test-report.json")

if not raw_path.exists():
    raw = {}
else:
    raw = json.loads(raw_path.read_text(encoding="utf-8"))

tests = []
for test in raw.get("tests", []):
    outcome = test.get("outcome", "unknown")
    call = test.get("call", {})
    setup = test.get("setup", {})
    failed_part = call if call.get("outcome") == "failed" else setup

    tests.append({
        "name": test.get("nodeid", "unknown"),
        "result": outcome,
        "failure_message": (
            failed_part.get("crash", {}).get("message")
            or failed_part.get("longrepr")
            if failed_part.get("outcome") == "failed"
            else None
        )
    })

summary = raw.get("summary", {})
total = summary.get("total", len(tests))
passed = sum(t["result"] == "passed" for t in tests)
failed = sum(t["result"] in ("failed", "error") for t in tests)
status = "passed" if failed == 0 and total > 0 and passed == total else "failed"

report = {
    "repository": os.getenv("GITHUB_REPOSITORY", "local"),
    "branch": os.getenv("GITHUB_REF_NAME", "local"),
    "commit_sha": os.getenv("GITHUB_SHA", "local"),
    "pipeline_run_id": os.getenv("GITHUB_RUN_ID", "local"),
    "execution_timestamp": datetime.now(timezone.utc).isoformat(),
    "tests": tests,
    "total": total,
    "passed": passed,
    "failed": failed,
    "overall_status": status
}

report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))

# A report must still be delivered if the tests fail.
import requests

receiver_url = os.getenv("REPORT_RECEIVER_URL", "http://127.0.0.1:5001/report")
try:
    response = requests.post(receiver_url, json=report, timeout=15)
    response.raise_for_status()
    print("Local report receiver:", response.text)
except requests.RequestException as exc:
    print("WARNING: Local report delivery failed:", exc)

sys.exit(0 if status == "passed" else 1)
