"""Dashboard Dash do histórico mensal salvo no Excel do Google Drive."""

from __future__ import annotations

from io import StringIO

import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, State, dash_table, dcc, html

from .sheets_repository import GoogleSheetsRepository
from .settings import AppSettings

METRICS = {
    "regular_market_price": "Preço (R$)",
    "regular_market_change_percent": "Variação diária (%)",
    "market_cap": "Valor de mercado (R$)",
    "regular_market_volume": "Volume",
    "price_earnings": "P/L",
    "earnings_per_share": "LPA",
    "fifty_two_week_low": "Mínima 52 semanas (R$)",
    "fifty_two_week_high": "Máxima 52 semanas (R$)",
}


def create_app(repository: GoogleSheetsRepository) -> Dash:
    """Cria o Dash; os dados e credenciais permanecem no processo Python."""

    initial_history = repository.load_history()
    tickers = sorted(initial_history["ticker"].dropna().unique().tolist())
    app = Dash(__name__, requests_pathname_prefix="/dash/")
    app.title = "Ações no Bolso"
    app.layout = html.Main(
        [
            html.H1("Ações no Bolso"),
            html.P("Histórico mensal de cotações armazenado no Google Drive."),
            html.Button("Recarregar dados", id="reload-button", n_clicks=0),
            html.Span(id="reload-status", style={"marginLeft": "1rem"}),
            dcc.Store(id="history-store", data=_frame_to_store(initial_history)),
            html.Div(
                [
                    html.Label("Tickers"),
                    dcc.Dropdown(
                        id="ticker-filter",
                        options=[{"label": ticker, "value": ticker} for ticker in tickers],
                        value=tickers,
                        multi=True,
                    ),
                    html.Label("Indicador", style={"marginTop": "1rem", "display": "block"}),
                    dcc.Dropdown(
                        id="metric-filter",
                        options=[{"label": label, "value": key} for key, label in METRICS.items()],
                        value="regular_market_price",
                        clearable=False,
                    ),
                ],
                style={"maxWidth": "720px", "marginTop": "1rem"},
            ),
            dcc.Graph(id="history-chart"),
            html.H2("Última fotografia por ticker"),
            dash_table.DataTable(
                id="latest-table",
                page_size=15,
                style_table={"overflowX": "auto"},
                style_cell={"textAlign": "left", "padding": "8px"},
            ),
        ],
        style={"maxWidth": "1200px", "margin": "2rem auto", "fontFamily": "Arial, sans-serif"},
    )

    @app.callback(
        Output("history-store", "data"),
        Output("reload-status", "children"),
        Output("ticker-filter", "options"),
        Output("ticker-filter", "value"),
        Input("reload-button", "n_clicks"),
        State("ticker-filter", "value"),
        prevent_initial_call=True,
    )
    def reload_history(_: int, selected_tickers: list[str] | None):
        history = repository.load_history()
        available = sorted(history["ticker"].dropna().unique().tolist())
        selected = [ticker for ticker in (selected_tickers or available) if ticker in available]
        return (
            _frame_to_store(history),
            f"Dados recarregados: {len(history)} linha(s).",
            [{"label": ticker, "value": ticker} for ticker in available],
            selected or available,
        )

    @app.callback(
        Output("history-chart", "figure"),
        Output("latest-table", "data"),
        Output("latest-table", "columns"),
        Input("history-store", "data"),
        Input("ticker-filter", "value"),
        Input("metric-filter", "value"),
    )
    def render_history(store_data: str, selected_tickers: list[str] | None, metric: str):
        history = _store_to_frame(store_data)
        filtered = history[history["ticker"].isin(selected_tickers or [])].copy()
        filtered["reference_month"] = pd.to_datetime(filtered["reference_month"])
        figure = px.line(
            filtered,
            x="reference_month",
            y=metric,
            color="ticker",
            markers=True,
            labels={"reference_month": "Mês", metric: METRICS[metric], "ticker": "Ticker"},
            title=METRICS[metric],
        )
        figure.update_layout(legend_title_text="Ticker")

        latest = (
            filtered.sort_values("reference_month")
            .groupby("ticker", as_index=False)
            .tail(1)
            .sort_values("ticker")
        )
        columns = [
            {"name": column.replace("_", " ").title(), "id": column}
            for column in latest.columns
        ]
        return figure, latest.to_dict("records"), columns

    return app


def _frame_to_store(frame: pd.DataFrame) -> str:
    return frame.to_json(orient="split", date_format="iso")


def _store_to_frame(data: str) -> pd.DataFrame:
    return pd.read_json(StringIO(data), orient="split")


def main() -> None:
    settings = AppSettings.from_environment()
    repository = GoogleSheetsRepository(
        credentials_file=settings.google_service_account_file,
        file_id=settings.google_drive_file_id,
        worksheet=settings.google_drive_worksheet,
    )
    create_app(repository).run(host=settings.dash_host, port=settings.dash_port, debug=False)


if __name__ == "__main__":
    main()
