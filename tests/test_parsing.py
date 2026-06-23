"""Testes do parser e da normalização — onde mora a qualidade de dados."""
from __future__ import annotations

from decimal import Decimal

import pytest
from bs4 import BeautifulSoup
from bs4.element import Tag

from app.collectors.parsing import (
    _extract_promotion_type,
    extract_item_id,
    parse_offers_html,
    parse_price,
)

# --- parse_price: locale BR (ponto de milhar, centavos separados) ---

@pytest.mark.parametrize(
    "fraction, cents, expected",
    [
        ("999", "90", Decimal("999.90")),
        ("1.299", "90", Decimal("1299.90")),     # ponto de milhar
        ("1.855", None, Decimal("1855.00")),     # sem centavos
        ("150", "", Decimal("150.00")),
        ("12.345.678", "05", Decimal("12345678.05")),  # ML sempre manda 2 dígitos de centavos
        (None, "90", None),
        ("", "90", None),
    ],
)
def test_parse_price(fraction, cents, expected):
    assert parse_price(fraction, cents) == expected


# --- extract_item_id: catálogo vs anúncio (namespaces distintos) ---

def test_extract_item_id_catalogo():
    url = "https://www.mercadolivre.com.br/fone-xyz/p/MLB111111"
    assert extract_item_id(url) == "MLB111111"


def test_extract_item_id_anuncio():
    url = "https://produto.mercadolivre.com.br/MLB-2222222-tenis-corrida"
    assert extract_item_id(url) == "MLB-2222222"


def test_extract_item_id_namespaces_nao_se_fundem():
    # mesmo número, namespaces diferentes -> ids diferentes
    assert extract_item_id(".../p/MLB123456") != extract_item_id(".../MLB-123456-x")


def test_extract_item_id_sem_id():
    assert extract_item_id("https://www.mercadolivre.com.br/ofertas") is None
    assert extract_item_id(None) is None


def test_extract_item_id_ignora_tokens_de_tracking():
    # URL com vários MLB nos params (deal/wid/tracking) -> pega o do produto (path), não o tracking
    u_cat = "https://www.mercadolivre.com.br/x/p/MLB55027309?deal=MLB779362&wid=MLB4620567101"
    u_anu = "https://produto.mercadolivre.com.br/MLB-4049279695-tenis?matt_tool=MLB-9999999"
    assert extract_item_id(u_cat) == "MLB55027309"
    assert extract_item_id(u_anu) == "MLB-4049279695"


def test_parse_offers_html_resiliente_a_excecao(ofertas_html, collected_at, monkeypatch):
    # Um card que estoura não pode derrubar a página inteira.
    import app.collectors.parsing as parsing

    real = parsing.parse_card
    calls = {"n": 0}

    def flaky(card, **kw):
        calls["n"] += 1
        if calls["n"] == 1:
            raise ValueError("card torto")
        return real(card, **kw)

    monkeypatch.setattr(parsing, "parse_card", flaky)
    prods = parsing.parse_offers_html(
        ofertas_html, source="ofertas", category="MLB1051",
        category_name="Celulares e Telefones", execution_id="e",
        collected_at=collected_at,
    )
    # O 1o card estourou e foi pulado; os demais válidos seguem (3 - 1 = 2).
    assert len(prods) == 2


# --- parse_offers_html: integração do parser contra a fixture ---

def test_parse_offers_html(ofertas_html, collected_at):
    prods = parse_offers_html(
        ofertas_html, source="ofertas", category="MLB1051",
        category_name="Celulares e Telefones", execution_id="exec123",
        collected_at=collected_at,
    )
    # Card 4 (sem título) é descartado -> 3 produtos
    assert len(prods) == 3

    by_id = {p.item_id: p for p in prods}

    # Card 1: catálogo, milhar+centavos, desconto calculado
    c1 = by_id["MLB111111"]
    assert c1.price == Decimal("999.90")
    assert c1.original_price == Decimal("1299.90")
    assert c1.discount_percent == pytest.approx(23.08, abs=0.01)
    assert c1.seller == "Loja Oficial XYZ"          # prefixo "Por " removido
    assert c1.image_url.endswith("mlb111111.webp")
    assert c1.is_real_promotion is True
    assert c1.dedupe_key == "mercado_livre_MLB111111_999.90"

    # Card 2: anúncio, sem centavos, imagem via data-src
    c2 = by_id["MLB-2222222"]
    assert c2.price == Decimal("150.00")
    assert c2.original_price == Decimal("300.00")
    assert c2.discount_percent == 50.0
    assert c2.image_url.endswith("mlb2222222.webp")
    assert c2.is_real_promotion is True

    # Card 3: sem desconto -> não é promoção real
    c3 = by_id["MLB333333"]
    assert c3.original_price is None
    assert c3.discount_percent is None
    assert c3.is_real_promotion is False


def test_filtra_so_promocoes_reais(ofertas_html, collected_at):
    prods = parse_offers_html(
        ofertas_html, source="ofertas", category="MLB1051",
        category_name="Celulares e Telefones", execution_id="exec123",
        collected_at=collected_at,
    )
    reais = [p for p in prods if p.is_real_promotion]
    assert len(reais) == 2  # cards 1 e 2 (card 3 sem desconto)


def test_parse_offers_html_carimba_categoria(ofertas_html, collected_at):
    prods = parse_offers_html(
        ofertas_html, source="s", category="MLB1648",
        category_name="Informática", execution_id="e", collected_at=collected_at,
    )
    assert prods
    assert all(p.category == "MLB1648" and p.category_name == "Informática" for p in prods)


# --- _extract_promotion_type: badge do card (por item) ---

def _card(inner: str) -> Tag:
    return BeautifulSoup(f'<div class="poly-card">{inner}</div>', "lxml").select_one(".poly-card")


def test_promotion_type_oferta_do_dia():
    card = _card('<span class="poly-component__highlight">OFERTA DO DIA</span>')
    assert _extract_promotion_type(card) == "OFERTA DO DIA"


def test_promotion_type_relampago_via_countdown():
    card = _card('<span class="poly-highlight-countdown__text">Oferta relâmpago</span>')
    assert _extract_promotion_type(card) == "OFERTA RELÂMPAGO"


def test_promotion_type_sem_badge_eh_none():
    assert _extract_promotion_type(_card("<span>sem badge</span>")) is None


def test_promotion_type_ignora_highlight_nao_promocional():
    card = _card('<span class="poly-component__highlight">MAIS VENDIDO</span>')
    assert _extract_promotion_type(card) is None
