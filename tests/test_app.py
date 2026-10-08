import json
import pytest
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_index_route(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Assignment Checker" in res.data

def test_api_status_route(client):
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.get_json()
    assert "has_api_key" in data
    assert "model_name" in data

def test_api_demo_master(client):
    res = client.get("/api/demo/master")
    assert res.status_code == 200
    data = res.get_json()
    assert "questions" in data
    assert len(data["questions"]) >= 4

def test_api_evaluate_demo(client):
    res = client.post("/api/evaluate", data={
        "use_demo_master": "true",
        "use_demo_students": "true",
        "strictness": "standard",
        "force_mock": "true"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["total_submissions"] == 3
    assert "results" in data
    assert len(data["results"]) == 3
    # Check that Alice, Bob, Charlie are in results
    names = [r["student_name"] for r in data["results"]]
    assert any("Alice" in n for n in names)
    assert any("Charlie" in n for n in names)

def test_api_export_csv_and_json(client):
    # First evaluate to populate LAST_EVALUATION
    client.post("/api/evaluate", data={
        "use_demo_master": "true",
        "use_demo_students": "true",
        "force_mock": "true"
    })

    # Test CSV export
    res_csv = client.get("/api/export/csv")
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.content_type
    assert b"Student ID" in res_csv.data

    # Test JSON export
    res_json = client.get("/api/export/json")
    assert res_json.status_code == 200
    assert "application/json" in res_json.content_type
    data = json.loads(res_json.data)
    assert data["total_submissions"] == 3

def test_api_evaluate_ai_direct(client):
    # Evaluate with AI Direct mode without any master solution
    res = client.post("/api/evaluate", data={
        "evaluation_mode": "ai_direct",
        "use_demo_students": "true",
        "subject_or_topic": "Computer Science",
        "force_mock": "true"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["evaluation_mode"] == "ai_direct"
    assert data["total_submissions"] == 3
    assert len(data["results"]) == 3
    assert data["results"][0]["evaluation_mode"] == "ai_direct"
