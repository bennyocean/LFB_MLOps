from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

### Unit Test for Prometheus Metrics Endpoint
def test_prometheus_metrics_endpoint():
    # Access the /metrics endpoint without authentication
    response = client.get("/metrics")

    # Ensure the response status code is 200 (Success)
    assert response.status_code == 200

    # Ensure the response contains Prometheus metrics data
    assert "http_request_duration_seconds" in response.text
    assert "http_requests_total" in response.text

    # Verify that the content-type starts with 'text/plain'
    assert response.headers["content-type"].startswith("text/plain")