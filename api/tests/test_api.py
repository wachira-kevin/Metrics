import datetime

def test_register(client):
    payload = {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "password123"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "userId" in data

def test_login(client, test_user):
    payload = {
        "username": "testuser",
        "password": "password123"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "accessToken" in data
    assert "refreshToken" in data
    assert data["tokenType"] == "bearer"

def test_ingest_metrics(client, test_app_token):
    payload = {
        "events": [
            {
                "eventType": "screen_view",
                "value": 1.0,
                "unit": "count",
                "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                "sessionId": "session-123",
                "deviceId": "device-456",
                "attributes": {"screen_name": "Home"}
            }
        ]
    }
    headers = {"app_token": test_app_token}
    response = client.post("/api/v1/ingest", json=payload, headers=headers)
    assert response.status_code == 202
    data = response.json()
    assert "accepted" in data
    assert data["accepted"] == 1

def test_metrics_summary(client, test_user):
    # Login to get token
    login_payload = {
        "username": "testuser",
        "password": "password123"
    }
    login_response = client.post("/api/v1/auth/login", json=login_payload)
    token = login_response.json()["accessToken"]
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/metrics/summary", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    # It should be a MetricsSummaryResponse object (dict in JSON)
    assert isinstance(data, dict)
