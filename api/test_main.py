import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.mark.parametrize("url, expected_status_code", [
    ("http://example.com", 200),               # Valid URL
    ("invalid-url", 422),                      # Invalid URL
    ("https://example.com/!@#$%^&*()", 200),   # URL with special characters
    ("https://пример.рф", 200),               # Non-ASCII URL
])
def test_generate_qr(url: str, expected_status_code: int):
    response = client.post("/generate-qr/", json={"url": url})

    assert response.status_code == expected_status_code

    if expected_status_code == 200:
        response_json = response.json()
        assert "qr_code_url" in response_json
        assert response_json["qr_code_url"].startswith("https")
