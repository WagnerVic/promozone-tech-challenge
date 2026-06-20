"""Pipeline: coleta → filtra promoções reais → (opcional) persiste no BigQuery."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from app.collectors.mercadolivre import MercadoLivreCollector
from app.core.logging import get_logger
from app.models.product import ProductSchema

logger = get_logger(__name__)


@dataclass
class PipelineResult:
    execution_id: str
    collected: int = 0
    promotions: int = 0
    filtered_out: int = 0
    inserted: int | None = None
    duplicates: int | None = None
    persisted: bool = False
    products: list[ProductSchema] = field(default_factory=list)

    def summary(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "collected": self.collected,
            "promotions": self.promotions,
            "filtered_out": self.filtered_out,
            "inserted": self.inserted,
            "duplicates": self.duplicates,
            "persisted": self.persisted,
        }


def run_pipeline(
    *,
    execution_id: str | None = None,
    sources: list[str] | None = None,
    max_pages: int | None = None,
    persist: bool = True,
) -> PipelineResult:
    execution_id = execution_id or str(uuid.uuid4())[:8]

    collector = MercadoLivreCollector(
        execution_id=execution_id, sources=sources, max_pages=max_pages
    )
    collected = collector.collect()
    promotions = [p for p in collected if p.is_real_promotion]

    result = PipelineResult(
        execution_id=execution_id,
        collected=len(collected),
        promotions=len(promotions),
        filtered_out=len(collected) - len(promotions),
        products=promotions,
    )

    if persist and promotions:
        from app.services.bigquery import BigQueryService  # import tardio: dry-run não usa GCP

        bq = BigQueryService()
        stats = bq.upsert(promotions, execution_id=execution_id)
        result.inserted = stats["inserted"]
        result.duplicates = stats["duplicates"]
        result.persisted = True
    elif persist and not promotions:
        logger.info("nothing to persist (0 promotions)", extra={"execution_id": execution_id})

    logger.info("pipeline complete", extra=result.summary())
    return result
