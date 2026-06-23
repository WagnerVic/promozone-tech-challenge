"""Coletor das vitrines de ofertas do Mercado Livre (httpx + retry/backoff)."""
from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.collectors.base import BaseCollector
from app.collectors.parsing import parse_offers_html
from app.core.config import resolve_category, settings
from app.core.logging import get_logger
from app.models.product import ProductSchema

logger = get_logger(__name__)

# Marcadores do muro anti-bot ("tráfego suspeito → login") do ML.
# Inclui as duas grafias: serviço `suspicious-traffic-frontend` (hífen) e path
# `/security/suspicious_traffic` (underscore) — robusto a qual aparece no corpo/URL.
_WALL_MARKERS = (
    "account-verification",
    "suspicious-traffic",
    "suspicious_traffic",
    "Para continuar, acesse sua conta",
)


def _looks_walled(url: str, html: str) -> bool:
    # A URL final (pós-redirect) é o sinal mais limpo; o corpo é o reforço.
    return any(m in url or m in html for m in _WALL_MARKERS)


def _is_transient(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TransportError):  # rede/timeout
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in (429, 500, 502, 503, 504)
    return False


class MercadoLivreCollector(BaseCollector):
    name = "mercado_livre_ofertas"

    def __init__(
        self,
        execution_id: str | None = None,
        sources: list[str] | None = None,
        max_pages: int | None = None,
    ):
        self.execution_id = execution_id or str(uuid.uuid4())[:8]
        self.sources = sources or settings.SOURCES
        self.max_pages = max_pages or settings.MAX_PAGES_PER_SOURCE
        self.walled = False
        self.headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        }

    def collect(self) -> list[ProductSchema]:
        logger.info(
            "collection started",
            extra={"execution_id": self.execution_id, "sources": self.sources},
        )
        seen: set[str] = set()
        products: list[ProductSchema] = []

        with httpx.Client(
            headers=self.headers,
            timeout=settings.REQUEST_TIMEOUT_SECONDS,
            follow_redirects=True,
        ) as client:
            for source in self.sources:
                products.extend(self._collect_source(client, source, seen))

        logger.info(
            "collection finished",
            extra={"execution_id": self.execution_id, "collected": len(products)},
        )
        return products

    def _collect_source(
        self, client: httpx.Client, source: str, seen: set[str]
    ) -> list[ProductSchema]:
        collected_at = datetime.now(UTC)
        category, category_name = resolve_category(source)
        out: list[ProductSchema] = []

        for page in range(1, self.max_pages + 1):
            try:
                resp = self._fetch(client, source, page)
            except httpx.HTTPError as exc:
                logger.error(
                    "page fetch failed",
                    extra={"execution_id": self.execution_id, "source": source,
                           "page": page, "error": str(exc)},
                    exc_info=True,
                )
                break

            html = resp.text
            page_products = parse_offers_html(
                html, source=source, category=category, category_name=category_name,
                execution_id=self.execution_id, collected_at=collected_at,
            )
            if not page_products:
                # 0 cards pode ser fim da paginação OU muro anti-bot — sinais distintos.
                if _looks_walled(str(resp.url), html):
                    self.walled = True
                    logger.warning(
                        "0 cards — possível muro anti-bot",
                        extra={"execution_id": self.execution_id, "source": source,
                               "page": page, "final_url": str(resp.url)},
                    )
                else:
                    logger.info(
                        "no products on page, stopping pagination",
                        extra={"execution_id": self.execution_id, "source": source, "page": page},
                    )
                break

            new = [p for p in page_products if p.dedupe_key not in seen]
            seen.update(p.dedupe_key for p in new)
            out.extend(new)
            logger.info(
                "page collected",
                extra={"execution_id": self.execution_id, "source": source, "page": page,
                       "found": len(page_products), "new": len(new)},
            )

            # Para se a página não trouxe nada novo (fim de paginação ou ?page ignorado).
            if not new:
                break
            if page < self.max_pages:
                time.sleep(settings.DELAY_BETWEEN_PAGES_SECONDS)

        return out

    @retry(
        retry=retry_if_exception(_is_transient),
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(min=settings.RETRY_MIN_SECONDS, max=settings.RETRY_MAX_SECONDS),
        reraise=True,
    )
    def _fetch(self, client: httpx.Client, source: str, page: int) -> httpx.Response:
        params = {"page": page} if page > 1 else None
        resp = client.get(source, params=params)
        resp.raise_for_status()
        return resp
