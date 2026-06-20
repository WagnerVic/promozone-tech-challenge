"""Parsing puro dos cards de oferta (sem rede → testável com fixtures)."""
from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from bs4 import BeautifulSoup
from bs4.element import Tag

from app.collectors import selectors as S
from app.core.logging import get_logger
from app.models.product import ProductSchema

logger = get_logger(__name__)

# Catálogo (/p/MLB123) e anúncio (MLB-123) são namespaces distintos — não fundir.
_RE_CATALOG = re.compile(r"/p/(MLB\d+)")
_RE_LISTING = re.compile(r"(MLB-\d{6,})")


def parse_price(fraction_text: str | None, cents_text: str | None) -> Decimal | None:
    """Combina inteiro + centavos no locale BR ('1.855' + '90' -> Decimal('1855.90'))."""
    if not fraction_text:
        return None
    digits = re.sub(r"[^\d]", "", fraction_text)
    if not digits:
        return None
    cents = re.sub(r"[^\d]", "", cents_text or "") or "00"
    cents = (cents + "00")[:2]
    return Decimal(f"{digits}.{cents}")


def extract_item_id(url: str | None) -> str | None:
    if not url:
        return None
    m = _RE_CATALOG.search(url)
    if m:
        return m.group(1)
    m = _RE_LISTING.search(url)
    if m:
        return m.group(1)
    return None


def _text(node: Tag | None) -> str | None:
    if node is None:
        return None
    return node.get_text(" ", strip=True) or None


def parse_card(
    card: Tag,
    *,
    source: str,
    execution_id: str,
    collected_at: datetime,
) -> ProductSchema | None:
    """Retorna None se faltar campo obrigatório (título/url/id/preço)."""
    title_tag = card.select_one(S.TITLE)
    if title_tag is None:
        return None
    title = _text(title_tag)
    url = title_tag.get("href")
    if not title or not url:
        return None

    item_id = extract_item_id(url)
    if not item_id:
        return None

    price = parse_price(
        _text(card.select_one(S.PRICE_CURRENT)),
        _text(card.select_one(S.PRICE_CURRENT_CENTS)),
    )
    if price is None:
        return None

    original_price = parse_price(
        _text(card.select_one(S.PRICE_PREVIOUS)),
        _text(card.select_one(S.PRICE_PREVIOUS_CENTS)),
    )

    seller = _text(card.select_one(S.SELLER))
    if seller and seller.lower().startswith("por "):
        seller = seller[4:].strip() or None

    image_url = None
    img = card.select_one(S.IMAGE)
    if img is not None:
        src = img.get("data-src") or img.get("src")
        if src and not src.startswith("data:"):
            image_url = src

    return ProductSchema(
        item_id=item_id,
        url=url,
        title=title,
        price=price,
        original_price=original_price,
        seller=seller,
        image_url=image_url,
        source=source,
        execution_id=execution_id,
        collected_at=collected_at,
    )


def parse_offers_html(
    html: str,
    *,
    source: str,
    execution_id: str,
    collected_at: datetime,
) -> list[ProductSchema]:
    soup = BeautifulSoup(html, "lxml")
    products: list[ProductSchema] = []
    for card in soup.select(S.CARD):
        try:
            product = parse_card(
                card, source=source, execution_id=execution_id, collected_at=collected_at
            )
        except Exception:
            # Um card torto não derruba a página inteira.
            logger.warning("card parse failed", exc_info=True)
            continue
        if product is not None:
            products.append(product)
    return products
