from __future__ import annotations

import httpx
import pytest

from acoes_no_bolso.brapi import (
    BrapiConfigurationError,
    BrapiHTTPError,
    BrapiResponseError,
    fetch_stock_quote,
)


def _client_with(handler: httpx.MockTransport) -> httpx.Client:
    return httpx.Client(transport=handler, base_url="https://brapi.dev")


def test_fetch_stock_quote_returns_first_result_data(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BRAPI_TOKEN", "test-token")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.url.path == "/api/v2/stocks/quote"
        assert request.url.params["symbols"] == "B3SA3"
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "requestedSymbol": "B3SA3",
                        "symbol": "B3SA3",
                        "changed": False,
                        "data": {"shortName": "B3", "regularMarketPrice": 12.34},
                    }
                ]
            },
        )

    with _client_with(httpx.MockTransport(handler)) as http_client:
        quote = fetch_stock_quote(" b3sa3 ", http_client=http_client)

    assert quote == {"shortName": "B3", "regularMarketPrice": 12.34}


def test_fetch_stock_quote_rejects_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BRAPI_TOKEN", raising=False)

    with _client_with(httpx.MockTransport(lambda _: httpx.Response(200))) as http_client:
        with pytest.raises(BrapiConfigurationError):
            fetch_stock_quote("B3SA3", http_client=http_client)


def test_fetch_stock_quote_raises_for_non_2xx(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BRAPI_TOKEN", "test-token")

    with _client_with(
        httpx.MockTransport(lambda _: httpx.Response(401, json={"message": "não autorizado"}))
    ) as http_client:
        with pytest.raises(BrapiHTTPError, match="HTTP 401"):
            fetch_stock_quote("B3SA3", http_client=http_client)


def test_fetch_stock_quote_requires_results_first_data(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BRAPI_TOKEN", "test-token")

    with _client_with(httpx.MockTransport(lambda _: httpx.Response(200, json={"results": []}))) as http_client:
        with pytest.raises(BrapiResponseError, match="não retornou resultados"):
            fetch_stock_quote("B3SA3", http_client=http_client)
