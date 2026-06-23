"""Configuração via variáveis de ambiente (12-factor)."""
from __future__ import annotations

import json
import re
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
)

# A categoria é metadado declarado (fonte da verdade): coletamos por recorte de
# categoria porque a vitrine não expõe a categoria por item. A URL é derivada daqui.
OFERTAS_URL = "https://www.mercadolivre.com.br/ofertas"
CATEGORIES = {
    "MLB1051": "Celulares e Telefones",
    "MLB1648": "Informática",
    "MLB5726": "Eletrodomésticos",
}
DEFAULT_SOURCES = [f"{OFERTAS_URL}?category={cid}" for cid in CATEGORIES]

_RE_CATEGORY = re.compile(r"[?&]category=(MLB\d+)")


def resolve_category(url: str) -> tuple[str, str]:
    """URL da fonte → (category_id, category_name). Único lugar que conhece a convenção."""
    m = _RE_CATEGORY.search(url or "")
    if m:
        cid = m.group(1)
        return cid, CATEGORIES.get(cid, cid)
    return "GERAL", "Ofertas (geral)"  # fonte sem ?category= (ex.: vitrine de teste)


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
