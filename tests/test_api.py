from fastapi.testclient import TestClient
from backend.main import app
client = TestClient(app)

def test_health():
    assert client.get("/api/v1/health").status_code == 200

def test_lookup_requires_fields():
    r = client.post("/api/v1/results/lookup", json={})
    assert r.status_code == 422