
import json
import app as portal

def test_valid_submission_is_saved_and_listed(tmp_path, monkeypatch):
    data_file = tmp_path / "submissions.json"
    monkeypatch.setattr(portal, "DATA_FILE", str(data_file))
    client = portal.app.test_client()

    response = client.post("/api/submissions", json={
        "name": "Ali",
        "registration_number": "FA23-BSE-001",
        "assignment_title": "DevOps Lab",
        "submission_url": "https://example.com/assignment"
    })

    assert response.status_code == 201
    assert response.json["message"] == "Submission saved successfully"

    listing = client.get("/api/submissions")
    assert listing.status_code == 200
    assert listing.json[0]["name"] == "Ali"

    saved = json.loads(data_file.read_text(encoding="utf-8"))
    assert len(saved) == 1

def test_missing_registration_number_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(portal, "DATA_FILE", str(tmp_path / "submissions.json"))
    client = portal.app.test_client()

    response = client.post("/api/submissions", json={
        "name": "Ali",
        "assignment_title": "DevOps Lab",
        "submission_url": "https://example.com/assignment"
    })

    assert response.status_code == 400
    assert "Registration Number is required" in response.json["message"]
    assert client.get("/api/submissions").json == []

def test_invalid_url_is_rejected_and_not_saved(tmp_path, monkeypatch):
    monkeypatch.setattr(portal, "DATA_FILE", str(tmp_path / "submissions.json"))
    client = portal.app.test_client()

    response = client.post("/api/submissions", json={
        "name": "Ali",
        "registration_number": "FA23-BSE-001",
        "assignment_title": "DevOps Lab",
        "submission_url": "not-a-valid-url"
    })

    assert response.status_code == 400
    assert response.json["message"] == "Invalid submission URL"
    assert client.get("/api/submissions").json == []
