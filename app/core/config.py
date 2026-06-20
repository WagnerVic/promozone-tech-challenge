"""Configuração via variáveis de ambiente (12-factor)."""
from __future__ import annotations

import json
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
)

DEFAULT_SOURCES = ["https://www.mercadolivre.com.br/ofertas"]


class Settings(BaseSettings):
    PROJECT_NAME: str = "Coletor de Promoções ML"
    APP_VERSION: str = "1.0.0"

    USER_AGENT: str = DEFAULT_USER_AGENT
    # NoDecode desliga o parse JSON automático para aceitarmos CSV no env (mais intuitivo).
    SOURCES: Annotated[list[str], NoDecode] = DEFAULT_SOURCES
    MAX_PAGES_PER_SOURCE: int = 5
    REQUEST_TIMEOUT_SECONDS: float = 20.0
    DELAY_BETWEEN_PAGES_SECONDS: float = 1.5
    MAX_RETRIES: int = 3
    RETRY_MIN_SECONDS: float = 2.0
    RETRY_MAX_SECONDS: float = 10.0

    # Nome padrão lido pelo SDK do GCP (auto-detecção). None -> SDK resolve via ADC/metadata.
    GOOGLE_CLOUD_PROJECT: str | None = None
    GCP_DATASET_ID: str = "promozone"
    BQ_TABLE: str = "promotions"
    BQ_LOCATION: str = "southamerica-east1"

    LOG_LEVEL: str = "INFO"

    @field_validator("SOURCES", mode="before")
    @classmethod
    def _split_sources(cls, v):
        # Aceita lista (Settings(SOURCES=[...])), JSON ('["a","b"]') ou CSV ("a,b").
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                return json.loads(v)
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )


settings = Settings()
