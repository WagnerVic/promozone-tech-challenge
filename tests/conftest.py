from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def ofertas_html() -> str:
    return (FIXTURES / "ofertas_sample.html").read_text(encoding="utf-8")


@pytest.fixture
def collected_at() -> datetime:
    return datetime(2026, 6, 20, 12, 0, 0, tzinfo=UTC)
