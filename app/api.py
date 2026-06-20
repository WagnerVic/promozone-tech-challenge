"""API HTTP (FastAPI) — camada fina sobre o pipeline.

Endpoints:
- GET  /health  → sinal de saúde (checa conexão com o BigQuery)
- POST /collect → dispara uma coleta (chama run_pipeline)

Autenticação é feita na borda (Cloud Run --no-allow-unauthenticated); o app não
implementa auth própria. Subir com: uvicorn app.api:app
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.models.api import CollectRequest, CollectResponse, HealthResponse
from app.pipeline import run_pipeline

configure_logging(settings.LOG_LEVEL)
logger = get_logger(__name__)

app = FastAPI(title=settings.PROJECT_NAME, version=settings.APP_VERSION)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    bigquery = "ok"
    try:
        from app.services.bigquery import BigQueryService

        # Ping leve: lista metadados (não roda query nem grava).
        list(BigQueryService().client.list_datasets(max_results=1))
    except Exception as exc:  # noqa: BLE001 - health agrega qualquer falha do BQ
        bigquery = f"erro: {exc}"
    status = "ok" if bigquery == "ok" else "degradado"
    return HealthResponse(status=status, bigquery=bigquery, version=settings.APP_VERSION)


@app.post("/collect", response_model=CollectResponse)
def collect(req: CollectRequest) -> CollectResponse:
    try:
        result = run_pipeline(
            sources=req.sources, max_pages=req.max_pages, persist=req.persist
        )
    except Exception as exc:
        logger.error("collect failed", extra={"error": str(exc)}, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return CollectResponse(**result.summary())
