"""Cliente tipado e seguro para a API de cotações da BRAPI."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from typing import NotRequired, TypedDict, cast

import httpx

BRAPI_QUOTE_URL = "https://brapi.dev/api/v2/stocks/quote"
_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9^]{1,12}$")


class StockQuoteData(TypedDict, total=False):
    """Campos conhecidos do objeto ``results[0].data`` da BRAPI."""

    shortName: str
    longName: str
    currency: str
    regularMarketPrice: float
    regularMarketChange: float
    regularMarketChangePercent: float
    regularMarketDayHigh: float
    regularMarketDayLow: float
    regularMarketDayRange: str
    regularMarketVolume: int
    marketCap: int
    regularMarketTime: str
    logoUrl: str
    exchange: str
    marketState: str
    fiftyTwoWeekLow: float
    fiftyTwoWeekHigh: float
    priceEarnings: NotRequired[float | None]
    earningsPerShare: NotRequired[float | None]


class BrapiError(RuntimeError):
    """Erro base da integração BRAPI."""


class BrapiConfigurationError(BrapiError):
    """O token necessário não está configurado no ambiente."""


class BrapiHTTPError(BrapiError):
    """A BRAPI retornou um código HTTP não bem-sucedido."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(f"BRAPI respondeu HTTP {status_code}: {detail}")
        self.status_code = status_code


class BrapiResponseError(BrapiError):
    """A resposta 2xx não seguiu o contrato esperado."""


def fetch_stock_quote(
    symbol: str,
    *,
    http_client: httpx.Client,
) -> StockQuoteData:
    """Busca uma cotação e devolve o objeto ``results[0].data``.

    O token é obtido somente da variável de ambiente ``BRAPI_TOKEN``. O cliente
    HTTP é recebido por injeção para seguir o padrão de cliente compartilhado da
    aplicação e permitir testes sem chamadas reais de rede.

    Raises:
        BrapiConfigurationError: se ``BRAPI_TOKEN`` não estiver definido.
        BrapiHTTPError: em qualquer resposta HTTP fora de 2xx.
        BrapiResponseError: se o JSON não contiver ``results[0].data``.
    """

    normalized_symbol = _normalize_symbol(symbol)
    token = os.getenv("BRAPI_TOKEN")
    if not token:
        raise BrapiConfigurationError(
            "Defina BRAPI_TOKEN no ambiente do processo antes de consultar a BRAPI."
        )

    try:
        response = http_client.get(
            BRAPI_QUOTE_URL,
            params={"symbols": normalized_symbol},
            headers={"Authorization": f"Bearer {token}"},
        )
    except httpx.HTTPError as exc:
        raise BrapiHTTPError(0, "falha de comunicação com a BRAPI") from exc

    if not response.is_success:
        raise BrapiHTTPError(response.status_code, _safe_error_detail(response))

    try:
        payload = response.json()
    except ValueError as exc:
        raise BrapiResponseError("A BRAPI retornou uma resposta 2xx sem JSON válido.") from exc

    return _first_quote_data(payload)


def _normalize_symbol(symbol: str) -> str:
    normalized_symbol = symbol.strip().upper()
    if not _SYMBOL_PATTERN.fullmatch(normalized_symbol):
        raise ValueError("Ticker inválido. Use de 1 a 12 caracteres A-Z, 0-9 ou ^.")
    return normalized_symbol


def _first_quote_data(payload: object) -> StockQuoteData:
    if not isinstance(payload, Mapping):
        raise BrapiResponseError("O corpo da BRAPI deve ser um objeto JSON.")

    results = payload.get("results")
    if not isinstance(results, list) or not results:
        raise BrapiResponseError("A BRAPI não retornou resultados para o ticker solicitado.")

    first_result = results[0]
    if not isinstance(first_result, Mapping):
        raise BrapiResponseError("O primeiro resultado da BRAPI é inválido.")

    data = first_result.get("data")
    if not isinstance(data, dict):
        raise BrapiResponseError("A BRAPI não retornou results[0].data para o ticker solicitado.")

    return cast(StockQuoteData, data)


def _safe_error_detail(response: httpx.Response) -> str:
    """Extrai um detalhe curto sem incluir cabeçalhos ou dados sensíveis."""

    try:
        body = response.json()
    except ValueError:
        body = None

    if isinstance(body, Mapping):
        message = body.get("message") or body.get("error")
        if isinstance(message, str) and message.strip():
            return message.strip()[:300]

    return "requisição não aceita"

