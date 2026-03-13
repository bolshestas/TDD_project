def test_stats_returns_200(client):
    shorten = client.post("/shorten", json={"url": "https://www.example.com"})
    code = shorten.json()["short_code"]
    response = client.get(f"/stats/{code}")
    assert response.status_code == 200


def test_stats_returns_correct_fields(client):
    shorten = client.post("/shorten", json={"url": "https://www.example.com"})
    code = shorten.json()["short_code"]
    response = client.get(f"/stats/{code}")
    data = response.json()
    assert "short_code" in data
    assert "original_url" in data
    assert "click_count" in data
    assert "created_at" in data


def test_stats_initial_click_count_is_zero(client):
    shorten = client.post("/shorten", json={"url": "https://www.example.com"})
    code = shorten.json()["short_code"]
    response = client.get(f"/stats/{code}")
    assert response.json()["click_count"] == 0


def test_stats_unknown_code_returns_404(client):
    response = client.get("/stats/unknown")
    assert response.status_code == 404


def test_stats_returns_correct_original_url(client):
    original = "https://www.example.com/some/path"
    shorten = client.post("/shorten", json={"url": original})
    code = shorten.json()["short_code"]
    response = client.get(f"/stats/{code}")
    assert response.json()["original_url"] == original
