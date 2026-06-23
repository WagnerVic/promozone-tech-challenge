"""Testes do parsing de SOURCES (lista / CSV / JSON)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings, resolve_category


def test_resolve_category_conhecida():
    cid, name = resolve_category("https://www.mercadolivre.com.br/ofertas?category=MLB1051")
    assert cid == "MLB1051"
    assert name == "Celulares e Telefones"


def test_resolve_category_id_desconhecido_usa_id_como_nome():
    cid, name = resolve_category("https://www.mercadolivre.com.br/ofertas?category=MLB9999&page=2")
    assert (cid, name) == ("MLB9999", "MLB9999")


def test_resolve_category_sem_param_fallback():
    assert resolve_category("https://www.mercadolivre.com.br/ofertas") == ("GERAL", "Ofertas (geral)")


def test_default_sources_sao_categorias():
    s = Settings(_env_file=None)
    assert 1 <= len(s.SOURCES) <= 3  # enunciado pede 1 a 3 fontes
    assert all("category=MLB" in u for u in s.SOURCES)


def test_sources_lista_direta():
    assert Settings(SOURCES=["a", "b"]).SOURCES == ["a", "b"]


def test_sources_csv(monkeypatch):
    monkeypatch.setenv("SOURCES", "https://a, https://b , https://c")
    assert Settings().SOURCES == ["https://a", "https://b", "https://c"]


def test_sources_json(monkeypatch):
    monkeypatch.setenv("SOURCES", '["https://a","https://b"]')
    assert Settings().SOURCES == ["https://a", "https://b"]


def test_sources_json_malformado_falha_previsivel(monkeypatch):
    monkeypatch.setenv("SOURCES", "[isso nao e json")
    with pytest.raises(ValidationError):
        Settings()
