import pytest
from unittest.mock import patch


def test_rate_limit_allows_requests_under_limit(client):
    """Requests under the limit should succeed."""
    with patch("app.middleware.rate_limit.RATE_LIMIT_REQUESTS", 5):
        for _ in range(3):
            response = client.post("/shorten", json={"url": "https://example.com"})
            assert response.status_code == 201


def test_rate_limit_blocks_requests_over_limit(client):
    """Requests over the limit should return 429."""
    with patch("app.middleware.rate_limit.RATE_LIMIT_REQUESTS", 3):
        for _ in range(3):
            client.post("/shorten", json={"url": "https://example.com"})
        response = client.post("/shorten", json={"url": "https://example.com"})
        assert response.status_code == 429


def test_rate_limit_response_contains_detail(client):
    """429 response should contain detail message."""
    with patch("app.middleware.rate_limit.RATE_LIMIT_REQUESTS", 1):
        client.post("/shorten", json={"url": "https://example.com"})
        response = client.post("/shorten", json={"url": "https://example.com"})
        assert "detail" in response.json()


def test_rate_limit_does_not_apply_to_redirect(client):
    """Rate limiting should not apply to redirect endpoint."""
    shorten = client.post("/shorten", json={"url": "https://example.com"})
    code = shorten.json()["short_code"]

    with patch("app.middleware.rate_limit.RATE_LIMIT_REQUESTS", 1):
        for _ in range(5):
            response = client.get(f"/{code}", follow_redirects=False)
            assert response.status_code == 302