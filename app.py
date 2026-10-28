
from flask import Flask, request, jsonify, render_template_string
from urllib.parse import urlparse
import json
import os

app = Flask(__name__)
DATA_FILE = os.path.join(os.path.dirname(__file__), "submissions.json")

HTML = """
<!doctype html>
<html>
<head>
    <title>Assignment Submission Portal</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; max-width: 750px; margin: 40px auto;
               padding: 20px; background: #f3f6fb; color: #182235; }
        form, .submission { background: white; padding: 20px; margin: 15px 0;
                            border-radius: 10px; }
        input { box-sizing: border-box; width: 100%; padding: 12px;
                margin: 8px 0 15px; }
        button { padding: 12px 20px; background: #155eef; color: white;
                 border: 0; cursor: pointer; }
        a { overflow-wrap: anywhere; }
    </style>
</head>
<body>
    <h1>Assignment Submission Portal</h1>
    <form id="submission-form">
        <label>Student Name</label>
        <input name="name" required>
        <label>Registration Number</label>
        <input name="registration_number" required>
        <label>Assignment Title</label>
        <input name="assignment_title" required>
        <label>Submission URL</label>
        <input name="submission_url" type="url" placeholder="https://example.com" required>
        <button type="submit">Submit Assignment</button>
        <p id="message"></p>
    </form>
    <h2>Saved Submissions</h2>
    <div id="submissions"></div>
    <script>
    async function loadSubmissions() {
        const response = await fetch('/api/submissions');
        const items = await response.json();
        document.getElementById('submissions').innerHTML = '';
        items.forEach(item => {
            const div = document.createElement('div');
            div.className = 'submission';
            const title = document.createElement('strong');
            title.textContent = item.assignment_title + ' — ' + item.name;
            const details = document.createElement('p');
            details.textContent = item.registration_number;
            const link = document.createElement('a');
            link.href = item.submission_url;
            link.textContent = item.submission_url;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            div.append(title, details, link);
            document.getElementById('submissions').appendChild(div);
        });
    }
    document.getElementById('submission-form').addEventListener('submit',
        async event => {
            event.preventDefault();
            const data = Object.fromEntries(new FormData(event.target));
            const response = await fetch('/api/submissions', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            const result = await response.json();
            document.getElementById('message').textContent =
                result.message || 'Submission saved';
            if (response.ok) {
                event.target.reset();
                loadSubmissions();
            }
        });
    loadSubmissions();
    </script>
</body>
</html>
"""

def read_submissions():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, encoding="utf-8") as file:
        return json.load(file)

def valid_url(value):
    try:
        parsed = urlparse(value or "")
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except (ValueError, TypeError):
        return False

@app.get("/")
def home():
    return render_template_string(HTML)

@app.get("/api/submissions")
def list_submissions():
    return jsonify(read_submissions())

@app.post("/api/submissions")
def create_submission():
    data = request.get_json(silent=True) or {}
    required = [
        "name", "registration_number",
        "assignment_title", "submission_url"
    ]

    for field in required:
        if not isinstance(data.get(field), str) or not data[field].strip():
            return jsonify({
                "message": f"{field.replace('_', ' ').title()} is required"
            }), 400

    if not valid_url(data["submission_url"].strip()):
        return jsonify({"message": "Invalid submission URL"}), 400

    submission = {
        field: data[field].strip() for field in required
    }
    submissions = read_submissions()
    submissions.append(submission)

    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(submissions, file, indent=2)

    return jsonify({
        "message": "Submission saved successfully",
        "submission": submission
    }), 201

if __name__ == "__main__":
    app.run(debug=True, port=5000)
