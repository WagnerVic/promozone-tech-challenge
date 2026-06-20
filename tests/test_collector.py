"""Testes de helpers do coletor (detecção de muro, retry transitório)."""
from __future__ import annotations

import httpx

from app.collectors.mercadolivre import _is_transient, _looks_walled


def test_muro_pela_url_final():
    assert _looks_walled("https://www.mercadolivre.com.br/gz/account-verification?go=x", "") is True


def test_muro_pelo_corpo():
    assert _looks_walled("https://x", "...Para continuar, acesse sua conta...") is True


def test_pagina_normal_nao_e_muro():
    assert _looks_walled("https://www.mercadolivre.com.br/ofertas", "<div class='poly-card'>") is False


def _status_error(code: int) -> httpx.HTTPStatusError:
    req = httpx.Request("GET", "https://x")
    return httpx.HTTPStatusError("e", request=req, response=httpx.Response(code, request=req))


def test_retry_so_no_transitorio():
    assert _is_transient(httpx.ConnectTimeout("t")) is True       # rede/timeout
    assert _is_transient(_status_error(503)) is True              # 5xx
    assert _is_transient(_status_error(429)) is True              # rate limit
    assert _is_transient(_status_error(403)) is False             # 4xx não re-tenta
    assert _is_transient(_status_error(404)) is False
