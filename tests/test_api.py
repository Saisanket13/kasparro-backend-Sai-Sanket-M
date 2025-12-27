from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200

def test_data():
    r = client.get("/data?limit=5")
    assert r.status_code == 200
