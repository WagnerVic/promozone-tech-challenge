"""Testes do parsing de SOURCES (lista / CSV / JSON)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings


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
