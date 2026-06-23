"""Seletores CSS dos cards da vitrine de ofertas do Mercado Livre.

Centralizados para facilitar manutenção quando o layout do ML muda.
"""
from __future__ import annotations

CARD = ".poly-card"
TITLE = "a.poly-component__title"
PRICE_CURRENT = ".poly-price__current .andes-money-amount__fraction"
PRICE_CURRENT_CENTS = ".poly-price__current .andes-money-amount__cents"
PRICE_PREVIOUS = ".andes-money-amount--previous .andes-money-amount__fraction"
PRICE_PREVIOUS_CENTS = ".andes-money-amount--previous .andes-money-amount__cents"
SELLER = ".poly-component__seller"
IMAGE = "img.poly-component__picture"
# Badge do tipo de promoção (ex.: "OFERTA DO DIA"); relâmpago usa o variante com cronômetro.
HIGHLIGHT = ".poly-component__highlight"
HIGHLIGHT_COUNTDOWN = ".poly-highlight-countdown__text"
