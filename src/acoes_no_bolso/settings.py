"""Configuração carregada exclusivamente do ambiente local do backend."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


class SettingsError(ValueError):
    """Variável de configuração obrigatória ausente ou inválida."""


@dataclass(frozen=True)
class AppSettings:
    """Configuração necessária para a coleta e o dashboard."""

    tickers: tuple[str, ...]
    google_service_account_file: Path
    google_drive_file_id: str
    google_drive_worksheet: str
    dash_host: str
    dash_port: int

    @classmethod
    def from_environment(cls) -> "AppSettings":
        load_dotenv()

        tickers = _parse_tickers(os.getenv("TICKERS", ""))
        service_account_file = Path(
            _required("GOOGLE_SERVICE_ACCOUNT_FILE")
        ).expanduser()
        drive_file_id = _required("GOOGLE_DRIVE_FILE_ID")
        worksheet = os.getenv("GOOGLE_DRIVE_WORKSHEET", "historico").strip()
        if not worksheet:
            raise SettingsError("GOOGLE_DRIVE_WORKSHEET não pode ser vazio.")

        try:
            dash_port = int(os.getenv("DASH_PORT", "8050"))
        except ValueError as exc:
            raise SettingsError("DASH_PORT deve ser um número inteiro.") from exc

        return cls(
            tickers=tickers,
            google_service_account_file=service_account_file,
            google_drive_file_id=drive_file_id,
            google_drive_worksheet=worksheet,
            dash_host=os.getenv("DASH_HOST", "127.0.0.1"),
            dash_port=dash_port,
        )


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SettingsError(f"Defina {name} no arquivo .env ou no ambiente.")
    return value


def _parse_tickers(value: str) -> tuple[str, ...]:
    tickers = tuple(
        dict.fromkeys(item.strip().upper() for item in value.split(",") if item.strip())
    )
    if not tickers:
        raise SettingsError("Defina ao menos um ticker em TICKERS.")
    return tickers
