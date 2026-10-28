"""Unit tests for the Streamlit UI helper functions.

Tests API healthcheck and review submission using mocked httpx responses.
"""

from unittest.mock import MagicMock, patch
import httpx
from interface.app import check_api_health, send_review


def test_check_api_health_success():
    """Returns parsed JSON when backend responds with 200 OK."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "ok", "banco": "conectado", "modelo": "carregado"}

    with patch("httpx.get", return_value=mock_response):
        health = check_api_health("http://fake-api:8000")
        assert health is not None
        assert health["status"] == "ok"


def test_check_api_health_failure():
    """Returns None when backend fails or is unreachable."""
    with patch("httpx.get", side_effect=httpx.ConnectError("Connection refused")):
        health = check_api_health("http://fake-api:8000")
        assert health is None


def test_send_review_success():
    """Returns 201 and created review payload on successful submission."""
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {
        "id": "6720c1f2e4b0a1d2c3e4f5a6",
        "texto": "Excelente fone de ouvido!",
        "produto": "Fone Bluetooth",
        "classe": "positivo",
        "confianca": 0.96,
        "modelo": "modelo_v1",
        "data": "2026-10-27T20:00:00Z",
    }

    with patch("httpx.post", return_value=mock_response):
        status_code, payload = send_review(
            api_url="http://fake-api:8000",
            text="Excelente fone de ouvido!",
            product="Fone Bluetooth",
        )
        assert status_code == 201
        assert payload["classe"] == "positivo"
        assert payload["confianca"] == 0.96


def test_send_review_connection_error():
    """Returns 503 status code when the API server is unreachable."""
    with patch("httpx.post", side_effect=httpx.ConnectError("Connection refused")):
        status_code, payload = send_review(
            api_url="http://fake-api:8000",
            text="Produto muito bom",
        )
        assert status_code == 503
        assert "Could not connect" in payload["erro"]


def test_send_review_timeout():
    """Returns 504 status code when the API request times out."""
    with patch("httpx.post", side_effect=httpx.TimeoutException("Timed out")):
        status_code, payload = send_review(
            api_url="http://fake-api:8000",
            text="Produto muito bom",
        )
        assert status_code == 504
        assert "timed out" in payload["erro"]
