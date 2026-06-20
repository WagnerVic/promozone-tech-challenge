"""Logging estruturado em JSON, compatível com Cloud Logging."""
from __future__ import annotations

import logging
import sys
from datetime import UTC, datetime

from pythonjsonlogger import json as jsonlogger


class JsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        # "time" (RFC3339) é o campo que o Cloud Logging usa como timestamp da entrada.
        log_record["time"] = datetime.fromtimestamp(record.created, UTC).isoformat().replace("+00:00", "Z")
        log_record["severity"] = record.levelname.upper()
        log_record["level"] = record.levelname.lower()
        log_record["module"] = record.name
        log_record.pop("asctime", None)


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    # Logs no stderr; stdout fica livre para dados (ex.: --dry-run | jq).
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter("%(message)s"))
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    for noisy in ("urllib3", "httpx", "httpcore", "google", "google.cloud"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
