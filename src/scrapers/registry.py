from __future__ import annotations
from typing import Type
from src.scrapers.base import BaseScraper

SCRAPER_REGISTRY: dict[str, Type[BaseScraper]] = {}


def register(key: str):
    """Decorator that registers a scraper class."""
    def decorator(cls: Type[BaseScraper]):
        SCRAPER_REGISTRY[key] = cls
        return cls
    return decorator
