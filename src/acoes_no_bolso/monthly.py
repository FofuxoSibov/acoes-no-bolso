"""Transformação e consolidação do histórico mensal de cotações."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
import pandas as pd

from .brapi import StockQuoteData, fetch_stock_quote

HISTORY_COLUMNS = [
    "reference_month",
    "collected_at",
    "ticker",
    "short_name",
    "currency",
    "regular_market_price",
    "regular_market_change",
    "regular_market_change_percent",
    "regular_market_day_high",
    "regular_market_day_low",
    "regular_market_volume",
    "market_cap",
    "price_earnings",
    "earnings_per_share",
    "fifty_two_week_low",
    "fifty_two_week_high",
]

NUMERIC_COLUMNS = [
    "regular_market_price",
    "regular_market_change",
    "regular_market_change_percent",
    "regular_market_day_high",
    "regular_market_day_low",
    "regular_market_volume",
    "market_cap",
    "price_earnings",
    "earnings_per_share",
    "fifty_two_week_low",
    "fifty_two_week_high",
]


def collect_monthly_quotes(
    tickers: tuple[str, ...],
    *,
    http_client: httpx.Client,
    collected_at: datetime | None = None,
) -> pd.DataFrame:
    """Busca cada ticker na BRAPI e cria a fotografia mensal em formato tabular."""

    timestamp = collected_at or datetime.now(ZoneInfo("America/Sao_Paulo"))
    rows = [
        _quote_to_row(ticker, fetch_stock_quote(ticker, http_client=http_client), timestamp)
        for ticker in tickers
    ]
    return pd.DataFrame(rows, columns=HISTORY_COLUMNS)


def merge_monthly_history(existing: pd.DataFrame, snapshot: pd.DataFrame) -> pd.DataFrame:
    """Atualiza o mês/ticker existente e preserva todo o histórico anterior."""

    _validate_snapshot(snapshot)
    current = _with_history_columns(existing)
    incoming = _with_history_columns(snapshot)
    combined = pd.concat([current, incoming], ignore_index=True)

    combined["reference_month"] = pd.to_datetime(
        combined["reference_month"], errors="raise"
    ).dt.strftime("%Y-%m-%d")
    combined["collected_at"] = pd.to_datetime(
        combined["collected_at"], errors="raise", utc=True
    ).dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    for column in NUMERIC_COLUMNS:
        combined[column] = pd.to_numeric(combined[column], errors="coerce")

    return (
        combined.sort_values(["ticker", "reference_month", "collected_at"])
        .drop_duplicates(subset=["ticker", "reference_month"], keep="last")
        .sort_values(["reference_month", "ticker"])
        .reset_index(drop=True)[HISTORY_COLUMNS]
    )


def _quote_to_row(ticker: str, quote: StockQuoteData, timestamp: datetime) -> dict[str, object]:
    return {
        "reference_month": timestamp.strftime("%Y-%m-%d"),
        "collected_at": timestamp.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ticker": ticker.upper(),
        "short_name": quote.get("shortName"),
        "currency": quote.get("currency"),
        "regular_market_price": quote.get("regularMarketPrice"),
        "regular_market_change": quote.get("regularMarketChange"),
        "regular_market_change_percent": quote.get("regularMarketChangePercent"),
        "regular_market_day_high": quote.get("regularMarketDayHigh"),
        "regular_market_day_low": quote.get("regularMarketDayLow"),
        "regular_market_volume": quote.get("regularMarketVolume"),
        "market_cap": quote.get("marketCap"),
        "price_earnings": quote.get("priceEarnings"),
        "earnings_per_share": quote.get("earningsPerShare"),
        "fifty_two_week_low": quote.get("fiftyTwoWeekLow"),
        "fifty_two_week_high": quote.get("fiftyTwoWeekHigh"),
    }


def _with_history_columns(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    for column in HISTORY_COLUMNS:
        if column not in result.columns:
            result[column] = pd.NA
    return result[HISTORY_COLUMNS]


def _validate_snapshot(snapshot: pd.DataFrame) -> None:
    missing = set(HISTORY_COLUMNS).difference(snapshot.columns)
    if missing:
        names = ", ".join(sorted(missing))
        raise ValueError(f"A fotografia mensal não possui as colunas obrigatórias: {names}.")
