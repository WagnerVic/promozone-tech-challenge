"""Schemas de entrada/saída da API (contrato HTTP, separado do modelo de domínio)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str          # "ok" | "degradado"
    bigquery: str        # "ok" ou a mensagem de erro
    version: str


class CollectRequest(BaseModel):
    max_pages: int | None = Field(default=None, ge=1, le=10)
    sources: list[str] | None = None
    persist: bool = True


class CollectResponse(BaseModel):
    execution_id: str
    collected: int
    promotions: int
    filtered_out: int
    inserted: int | None = None
    duplicates: int | None = None
    persisted: bool
    walled: bool = False
