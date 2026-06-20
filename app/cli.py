"""CLI do coletor.

    python -m app.cli --dry-run     # coleta+normaliza, imprime JSON, sem GCP
    python -m app.cli               # coleta e persiste no BigQuery
"""
from __future__ import annotations

import argparse
import json
import sys

from app.core.config import settings
from app.core.logging import configure_logging
from app.pipeline import run_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Coletor de promoções do Mercado Livre")
    parser.add_argument("--dry-run", action="store_true", help="Não persiste no BigQuery.")
    parser.add_argument("--max-pages", type=int, default=None, help="Máx. páginas por fonte.")
    parser.add_argument(
        "--source", action="append", dest="sources", default=None,
        help="URL de vitrine de ofertas (repetível).",
    )
    parser.add_argument("--limit", type=int, default=5, help="Qtde a imprimir no --dry-run.")
    args = parser.parse_args(argv)

    configure_logging(settings.LOG_LEVEL)

    result = run_pipeline(
        sources=args.sources, max_pages=args.max_pages, persist=not args.dry_run
    )

    output = {
        "summary": result.summary(),
        "sample": [p.model_dump(mode="json") for p in result.products[: args.limit]],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
