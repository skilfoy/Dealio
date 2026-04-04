import logging
from typing import Type

logger = logging.getLogger(__name__)

SCRAPER_REGISTRY: dict[str, Type] = {}


def register_scraper(slug: str):
    """Decorator to register a scraper class for a retailer slug."""
    def wrapper(cls):
        SCRAPER_REGISTRY[slug] = cls
        logger.debug("Registered scraper: %s -> %s", slug, cls.__name__)
        return cls
    return wrapper


def get_scraper(slug: str) -> Type | None:
    return SCRAPER_REGISTRY.get(slug)


def get_all_scrapers() -> dict[str, Type]:
    return dict(SCRAPER_REGISTRY)
