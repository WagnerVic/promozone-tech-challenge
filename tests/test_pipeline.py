"""Testes do PipelineResult (sem rede/GCP)."""
from __future__ import annotations

from app import pipeline
from app.models.api import CollectResponse
from app.pipeline import PipelineResult


def test_summary_tem_walled():
    r = PipelineResult(execution_id="x")
    s = r.summary()
    assert s["walled"] is False
    assert set(s) == {
        "execution_id", "collected", "promotions", "filtered_out",
        "inserted", "duplicates", "persisted", "walled",
    }


def test_walled_propaga_collector_ate_response(monkeypatch):
    # Prova de propagação por observação: só um walled=True viajando confirma o fio
    # collector → PipelineResult → summary() → CollectResponse. (walled=False não
    # discrimina: CollectResponse.walled tem default False e mascararia a ausência.)
    class _WalledCollector:
        def __init__(self, **kw):
            self.walled = True

        def collect(self):
            return []

    monkeypatch.setattr(pipeline, "MercadoLivreCollector", _WalledCollector)
    result = pipeline.run_pipeline(persist=False)

    assert result.walled is True                                # collector → PipelineResult
    assert result.summary()["walled"] is True                  # → summary()
    assert CollectResponse(**result.summary()).walled is True  # → CollectResponse (API)
