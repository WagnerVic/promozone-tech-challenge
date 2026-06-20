"""Testes do PipelineResult (sem rede/GCP)."""
from __future__ import annotations

from app.pipeline import PipelineResult


def test_summary_tem_walled():
    r = PipelineResult(execution_id="x")
    s = r.summary()
    assert s["walled"] is False
    assert set(s) == {
        "execution_id", "collected", "promotions", "filtered_out",
        "inserted", "duplicates", "persisted", "walled",
    }
