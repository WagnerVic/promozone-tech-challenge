"""Contrato modelo <-> schema da staging (puro, sem GCP).

Garante que os campos serializados do ProductSchema batem 1:1 com a staging —
divergência quebraria o load job (campo desconhecido ou REQUIRED faltando).
"""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.models.product import ProductSchema
from app.services.bigquery import _STAGING_SCHEMA


def _product() -> ProductSchema:
    return ProductSchema(
        item_id="MLB1", url="u", title="t", price=Decimal("10.00"),
        source="s", category="MLB1051", category_name="Celulares e Telefones",
        execution_id="e", collected_at=datetime(2026, 6, 20, tzinfo=UTC),
    )


def test_model_bate_com_staging_schema():
    assert set(_product().model_dump(mode="json")) == {f.name for f in _STAGING_SCHEMA}


def test_dedupe_key_presente_no_schema():
    # o MERGE casa por dedupe_key — ele tem que existir na staging
    assert "dedupe_key" in {f.name for f in _STAGING_SCHEMA}
