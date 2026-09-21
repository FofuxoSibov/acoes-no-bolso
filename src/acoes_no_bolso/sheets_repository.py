"""Repositório de histórico armazenado de forma nativa no Google Sheets."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import gspread
import pandas as pd
from gspread_dataframe import get_as_dataframe, set_with_dataframe

from .monthly import HISTORY_COLUMNS, merge_monthly_history


class GoogleSheetsRepository:
    """Lê e atualiza uma aba de um arquivo Google Sheets."""

    def __init__(self, *, credentials_file: Path, file_id: str, worksheet: str) -> None:
        self._credentials_file = credentials_file
        self._file_id = file_id
        self._worksheet = worksheet
        self._client: gspread.Client | None = None

    def load_history(self) -> pd.DataFrame:
        """Baixa do Google Sheets e retorna a aba de histórico normalizada."""
        sheet = self._get_worksheet()
        try:
            history = get_as_dataframe(sheet, evaluate_formulas=True)
        except Exception as exc:
            raise ValueError("Erro ao carregar dados do Google Sheets.") from exc
            
        # Limpar linhas e colunas vazias geradas pelo gspread_dataframe
        history = history.dropna(how='all')
        
        # O Sheets pode retornar dados vazios inicialmente
        if history.empty:
            history = pd.DataFrame(columns=HISTORY_COLUMNS)
            
        return self._normalize_history(history)

    def upsert_snapshot(self, snapshot: pd.DataFrame) -> pd.DataFrame:
        """Mescla a fotografia e atualiza a planilha."""
        merged = merge_monthly_history(self.load_history(), snapshot)
        self._upload_history(merged)
        return merged

    def _upload_history(self, history: pd.DataFrame) -> None:
        sheet = self._get_worksheet()
        # Limpa o conteúdo existente para não sobrar lixo e ajusta o dataframe novo
        sheet.clear()
        set_with_dataframe(sheet, history)

    def _get_worksheet(self) -> gspread.worksheet.Worksheet:
        if self._client is None:
            if not self._credentials_file.is_file():
                raise FileNotFoundError(
                    f"Arquivo de credenciais não encontrado: {self._credentials_file}"
                )
            self._client = gspread.service_account(filename=str(self._credentials_file))
        
        spreadsheet = self._client.open_by_key(self._file_id)
        try:
            return spreadsheet.worksheet(self._worksheet)
        except gspread.exceptions.WorksheetNotFound:
            # Cria a aba se não existir
            return spreadsheet.add_worksheet(title=self._worksheet, rows=1000, cols=20)

    @staticmethod
    def _normalize_history(history: pd.DataFrame) -> pd.DataFrame:
        result = history.copy()
        for column in HISTORY_COLUMNS:
            if column not in result.columns:
                result[column] = pd.NA
        return result[HISTORY_COLUMNS]

