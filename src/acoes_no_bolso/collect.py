"""Comando de coleta mensal BRAPI -> Excel no Google Drive."""

from __future__ import annotations

import argparse

from .drive_excel import GoogleDriveExcelRepository
from .http_client import create_http_client
from .monthly import collect_monthly_quotes
from .settings import AppSettings


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Coleta cotações mensais da BRAPI.")
    parser.add_argument(
        "--tickers",
        nargs="+",
        help="Sobrescreve os tickers configurados em TICKERS.",
    )
    args = parser.parse_args(argv)

    settings = AppSettings.from_environment()
    tickers = tuple(item.strip().upper() for item in args.tickers) if args.tickers else settings.tickers

    with create_http_client() as http_client:
        snapshot = collect_monthly_quotes(tickers, http_client=http_client)

    repository = GoogleDriveExcelRepository(
        credentials_file=settings.google_service_account_file,
        file_id=settings.google_drive_file_id,
        worksheet=settings.google_drive_worksheet,
    )
    history = repository.upsert_snapshot(snapshot)
    print(f"Coleta concluída: {len(snapshot)} ticker(s), {len(history)} linha(s) no histórico.")


if __name__ == "__main__":
    main()
