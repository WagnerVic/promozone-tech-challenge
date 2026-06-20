"""Interface de coletor."""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.product import ProductSchema


class BaseCollector(ABC):
    name: str
    walled: bool = False  # True se a coleta detectou muro anti-bot

    @abstractmethod
    def collect(self) -> list[ProductSchema]:
        raise NotImplementedError
