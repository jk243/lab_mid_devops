
from flask import Flask, request, jsonify
from pathlib import Path
import json

app = Flask(__name__)
REPORT_FILE = Path(__file__).resolve().parent.parent / "test-report.json"

@app.post("/report")
def receive_report():
    report = request.get_json(silent=True)

    if not isinstance(report, dict) or "tests" not in report:
        return jsonify({"error": "Invalid test report"}), 400

    REPORT_FILE.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8"
    )
    return jsonify({
        "message": "Report saved",
        "file": str(REPORT_FILE)
    }), 200

@app.get("/health")
def health():
    return jsonify({"status": "ready"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001)
