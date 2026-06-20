"""Teste estrutural da API (sem subir servidor nem acessar GCP)."""
from __future__ import annotations

from app.api import app


def test_rotas_existem():
    paths = {r.path for r in app.routes}
    assert "/health" in paths
    assert "/collect" in paths
