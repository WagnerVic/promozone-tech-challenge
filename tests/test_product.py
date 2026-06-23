"""Testes do contrato do ProductSchema (dinheiro, desconto derivado, tz, dedupe)."""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.product import ProductSchema

_AT = datetime(2026, 6, 20, 12, 0, 0, tzinfo=UTC)


def _make(**kw) -> ProductSchema:
    base = dict(
        item_id="MLB1", url="u", title="t", price=Decimal("100.00"),
        source="s", category="MLB1051", category_name="Celulares e Telefones",
        execution_id="e", collected_at=_AT,
    )
    base.update(kw)
    return ProductSchema(**base)


def test_discount_percent_derivado():
    p = _make(price=Decimal("999.90"), original_price=Decimal("1299.90"))
    assert p.discount_percent == pytest.approx(23.08, abs=0.01)


def test_discount_percent_none_sem_original():
    assert _make(original_price=None).discount_percent is None


def test_is_real_promotion():
    assert _make(price=Decimal("80"), original_price=Decimal("100")).is_real_promotion is True
    assert _make(price=Decimal("100"), original_price=None).is_real_promotion is False
    assert _make(price=Decimal("100"), original_price=Decimal("100")).is_real_promotion is False


def test_price_serializa_como_string():
    # Decimal -> string em mode="json" => BQ carrega string->NUMERIC de forma exata.
    d = _make(price=Decimal("755.65"), original_price=Decimal("1855.00")).model_dump(mode="json")
    assert d["price"] == "755.65"
    assert d["original_price"] == "1855.00"


def test_collected_at_naive_rejeitado():
    with pytest.raises(ValidationError):
        _make(collected_at=datetime(2026, 6, 20, 12, 0, 0))


def test_dedupe_key_formato():
    assert _make(price=Decimal("755.65")).dedupe_key == "mercado_livre_MLB1_755.65"
