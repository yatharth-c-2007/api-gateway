import pytest
from unittest.mock import patch, MagicMock
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def _mock_response(status_code, text):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    return resp


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200


@patch("app.requests.post")
def test_create_order_forwards_to_order_service(mock_post, client):
    mock_post.return_value = _mock_response(201, '{"order_id": "abc", "status": "confirmed"}')
    resp = client.post("/api/orders", json={"item_id": "sku-001", "quantity": 1})
    assert resp.status_code == 201
    mock_post.assert_called_once()


@patch("app.requests.post")
def test_create_order_downstream_unavailable(mock_post, client):
    import requests as real_requests
    mock_post.side_effect = real_requests.exceptions.ConnectionError("boom")
    resp = client.post("/api/orders", json={"item_id": "sku-001", "quantity": 1})
    assert resp.status_code == 503


@patch("app.requests.get")
def test_get_order_forwards(mock_get, client):
    mock_get.return_value = _mock_response(200, '{"order_id": "abc"}')
    resp = client.get("/api/orders/abc")
    assert resp.status_code == 200
