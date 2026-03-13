import pytest


def test_shorten_returns_201(client):
    response = client.post("/shorten", json={"url": "https://www.example.com"})
    assert response.status_code == 201


def test_shorten_returns_short_code(client):
    response = client.post("/shorten", json={"url": "https://www.example.com"})
    data = response.json()
    assert "short_code" in data
    assert len(data["short_code"]) == 6


def test_shorten_returns_short_url(client):
    response = client.post("/shorten", json={"url": "https://www.example.com"})
    data = response.json()
    assert "short_url" in data
    assert data["short_code"] in data["short_url"]


def test_shorten_returns_original_url(client):
    original = "https://www.example.com"
    response = client.post("/shorten", json={"url": original})
    assert response.json()["original_url"] == original


def test_shorten_rejects_invalid_url(client):
    response = client.post("/shorten", json={"url": "not-a-valid-url"})
    assert response.status_code == 422


def test_shorten_rejects_empty_url(client):
    response = client.post("/shorten", json={"url": ""})
    assert response.status_code == 422


def test_shorten_generates_unique_codes(client):
    urls = [f"https://example.com/page{i}" for i in range(10)]
    codes = set()
    for url in urls:
        response = client.post("/shorten", json={"url": url})
        codes.add(response.json()["short_code"])
    assert len(codes) == 10


def test_same_url_gets_different_codes(client):
    url = "https://www.example.com"
    r1 = client.post("/shorten", json={"url": url})
    r2 = client.post("/shorten", json={"url": url})
    assert r1.json()["short_code"] != r2.json()["short_code"]
