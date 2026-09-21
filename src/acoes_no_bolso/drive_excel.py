"""Repositório de histórico Excel (.xlsx) armazenado no Google Drive."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

from .monthly import HISTORY_COLUMNS, merge_monthly_history

DRIVE_SCOPE = "https://www.googleapis.com/auth/drive"
EXCEL_MIME_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class GoogleDriveExcelRepository:
    """Lê e atualiza uma aba de um arquivo Excel existente no Google Drive."""

    def __init__(self, *, credentials_file: Path, file_id: str, worksheet: str) -> None:
        self._credentials_file = credentials_file
        self._file_id = file_id
        self._worksheet = worksheet
        self._service: Any | None = None

    def load_history(self) -> pd.DataFrame:
        """Baixa o Excel e retorna a aba de histórico normalizada."""

        content = self._download_file()
        try:
            history = pd.read_excel(content, sheet_name=self._worksheet)
        except ValueError as exc:
            raise ValueError(
                f"A aba '{self._worksheet}' não existe no arquivo Excel do Drive."
            ) from exc
        return self._normalize_history(history)

    def upsert_snapshot(self, snapshot: pd.DataFrame) -> pd.DataFrame:
        """Mescla a fotografia e envia uma nova revisão do mesmo arquivo Excel."""

        merged = merge_monthly_history(self.load_history(), snapshot)
        self._upload_history(merged)
        return merged

    def _download_file(self) -> BytesIO:
        request = self._drive.files().get_media(
            fileId=self._file_id,
            supportsAllDrives=True,
        )
        destination = BytesIO()
        downloader = MediaIoBaseDownload(destination, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        destination.seek(0)
        return destination

    def _upload_history(self, history: pd.DataFrame) -> None:
        content = BytesIO()
        export = history.where(pd.notna(history), None)
        with pd.ExcelWriter(content, engine="openpyxl") as writer:
            export.to_excel(writer, sheet_name=self._worksheet, index=False)

        content.seek(0)
        media = MediaIoBaseUpload(content, mimetype=EXCEL_MIME_TYPE, resumable=False)
        self._drive.files().update(
            fileId=self._file_id,
            media_body=media,
            supportsAllDrives=True,
        ).execute()

    @property
    def _drive(self) -> Any:
        if self._service is None:
            if not self._credentials_file.is_file():
                raise FileNotFoundError(
                    f"Arquivo de credenciais não encontrado: {self._credentials_file}"
                )
            credentials = Credentials.from_service_account_file(
                self._credentials_file,
                scopes=[DRIVE_SCOPE],
            )
            self._service = build("drive", "v3", credentials=credentials, cache_discovery=False)
        return self._service

    @staticmethod
    def _normalize_history(history: pd.DataFrame) -> pd.DataFrame:
        result = history.copy()
        for column in HISTORY_COLUMNS:
            if column not in result.columns:
                result[column] = pd.NA
        return result[HISTORY_COLUMNS]
