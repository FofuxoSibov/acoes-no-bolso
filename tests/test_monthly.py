from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from acoes_no_bolso.monthly import HISTORY_COLUMNS, collect_monthly_quotes, merge_monthly_history


def test_collect_monthly_quotes_maps_brapi_data(monkeypatch) -> None:
    def fake_fetch(ticker: str, *, http_client: object):
        assert ticker == "B3SA3"
        assert http_client is client
        return {
            "shortName": "B3",
            "currency": "BRL",
            "regularMarketPrice": 12.34,
            "marketCap": 99_000_000,
        }

    client = object()
    monkeypatch.setattr("acoes_no_bolso.monthly.fetch_stock_quote", fake_fetch)
    result = collect_monthly_quotes(
        ("B3SA3",),
        http_client=client,
        collected_at=datetime(2026, 9, 15, 10, tzinfo=ZoneInfo("America/Sao_Paulo")),
    )

    assert result.loc[0, "reference_month"] == "2026-09-01"
    assert result.loc[0, "regular_market_price"] == 12.34
    assert list(result.columns) == HISTORY_COLUMNS


def test_merge_monthly_history_replaces_same_ticker_and_month() -> None:
    existing = pd.DataFrame([{column: None for column in HISTORY_COLUMNS}])
    existing.loc[0, ["reference_month", "collected_at", "ticker", "regular_market_price"]] = [
        "2026-09-01",
        "2026-09-01T13:00:00Z",
        "B3SA3",
        10.0,
    ]
    snapshot = existing.copy()
    snapshot.loc[0, ["collected_at", "regular_market_price"]] = [
        "2026-09-15T13:00:00Z",
        12.34,
    ]

    result = merge_monthly_history(existing, snapshot)

    assert len(result) == 1
    assert result.loc[0, "regular_market_price"] == 12.34
