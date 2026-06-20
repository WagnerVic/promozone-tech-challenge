"""Modelo de domínio normalizado de uma promoção."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, computed_field, field_validator

MARKETPLACE = "mercado_livre"


class ProductSchema(BaseModel):
    marketplace: str = Field(default=MARKETPLACE)
    item_id: str
    url: str
    title: str
    price: Decimal
    original_price: Decimal | None = None
    seller: str | None = None
    image_url: str | None = None
    source: str
    currency: str = "BRL"

    execution_id: str
    collected_at: datetime

    @field_validator("collected_at")
    @classmethod
    def _require_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("collected_at deve ser tz-aware (UTC)")
        return v

    @computed_field  # type: ignore[prop-decorator]
    @property
    def discount_percent(self) -> float | None:
        if self.original_price is None or self.original_price <= self.price:
            return None
        return round(float((self.original_price - self.price) / self.original_price * 100), 2)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def dedupe_key(self) -> str:
        # Inclui o preço: mesmo item com preço novo = linha nova (histórico de preços).
        return f"{self.marketplace}_{self.item_id}_{self.price:.2f}"

    @property
    def is_real_promotion(self) -> bool:
        return self.original_price is not None and self.original_price > self.price
