from django.test import Client


def test_health_endpoint_returns_ok():
    response = Client(HTTP_HOST="localhost").get("/health/")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "support-operations-copilot",
    }
