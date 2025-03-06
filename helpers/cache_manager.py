from django.conf import settings
from django.core.cache import cache
from typing import Any


class CacheManager:
    @classmethod
    def set_key(cls, key: str, data: Any, timeout: int = None) -> None:
        key = f"{settings.ENVIRONMENT}:{key}"
        cache.set(key, data, timeout=timeout)

    @classmethod
    def retrieve_key_ttl(cls, key: str) -> int:
        key = f"{settings.ENVIRONMENT}:{key}"
        return cache.ttl(key)

    @classmethod
    def retrieve_key(cls, key: str) -> Any:
        key = f"{settings.ENVIRONMENT}:{key}"
        return cache.get(key)

    @classmethod
    def delete_key(cls, key: str) -> None:
        key = f"{settings.ENVIRONMENT}:{key}"
        cache.delete(key)