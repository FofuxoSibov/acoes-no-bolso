"""API FastAPI para a aplicação Ações no Bolso e entrypoint integrado."""

from __future__ import annotations

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from .settings import AppSettings
from .sheets_repository import GoogleSheetsRepository
from .monthly import collect_monthly_quotes
from fastapi.responses import FileResponse
from .dashboard import create_app
import os

static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")

app = FastAPI(title="API Ações no Bolso")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(static_dir, "index.html"))

# Variáveis globais para injeção simples
settings: AppSettings = None
repository: GoogleSheetsRepository = None

@app.on_event("startup")
def startup_event():
    global settings, repository
    settings = AppSettings.from_environment()
    repository = GoogleSheetsRepository(
        credentials_file=settings.google_service_account_file,
        file_id=settings.google_drive_file_id,
        worksheet=settings.google_drive_worksheet,
    )
    
    # Monta o app Dash
    try:
        dash_app = create_app(repository)
        app.mount("/dash", WSGIMiddleware(dash_app.server))
    except Exception as e:
        import logging
        logging.warning(f"Não foi possível inicializar o dashboard Dash. Erro: {e}")

@app.post("/api/collect")
def collect_data():
    """Aciona a coleta da BRAPI para todos os tickers e atualiza o Sheets."""
    try:
        with httpx.Client() as client:
            snapshot = collect_monthly_quotes(settings.tickers, http_client=client)
        merged = repository.upsert_snapshot(snapshot)
        return {"status": "success", "rows_updated": len(merged)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history")
def get_history():
    """Retorna o histórico atual persistido no Google Sheets."""
    try:
        import math
        history = repository.load_history()
        records = history.to_dict(orient="records")
        for row in records:
            for key, value in row.items():
                if isinstance(value, float) and math.isnan(value):
                    row[key] = None
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def main() -> None:
    settings = AppSettings.from_environment()
    uvicorn.run("acoes_no_bolso.api:app", host=settings.dash_host, port=settings.dash_port, reload=True)

if __name__ == "__main__":
    main()

