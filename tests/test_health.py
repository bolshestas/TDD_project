def test_health_check_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_check_returns_ok_status(client):
    response = client.get("/health")
    assert response.json()["status"] == "ok"


def test_health_check_returns_version(client):
    response = client.get("/health")
    assert "version" in response.json()
