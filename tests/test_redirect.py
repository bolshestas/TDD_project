def test_redirect_returns_302(client):
    shorten = client.post("/shorten", json={"url": "https://www.example.com"})
    code = shorten.json()["short_code"]
    response = client.get(f"/{code}", follow_redirects=False)
    assert response.status_code == 302


def test_redirect_location_is_original_url(client):
    original = "https://www.example.com"
    shorten = client.post("/shorten", json={"url": original})
    code = shorten.json()["short_code"]
    response = client.get(f"/{code}", follow_redirects=False)
    assert response.headers["location"] == original


def test_redirect_unknown_code_returns_404(client):
    response = client.get("/nonexistent", follow_redirects=False)
    assert response.status_code == 404


def test_redirect_increments_click_count(client):
    shorten = client.post("/shorten", json={"url": "https://www.example.com"})
    code = shorten.json()["short_code"]

    client.get(f"/{code}", follow_redirects=False)
    client.get(f"/{code}", follow_redirects=False)

    stats = client.get(f"/stats/{code}")
    assert stats.json()["click_count"] == 2
