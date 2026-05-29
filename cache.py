"""
Cache simples com TTL (Time To Live) em memória.
Evita chamadas repetidas às APIs externas e respeita rate limits.
"""

import time
from typing import Any


class TTLCache:
    def __init__(self):
        self._store: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Any | None:
        if key in self._store:
            value, expires_at = self._store[key]
            if time.time() < expires_at:
                return value
            del self._store[key]
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 1800):
        self._store[key] = (value, time.time() + ttl_seconds)

    def delete(self, key: str):
        self._store.pop(key, None)

    def clear(self):
        self._store.clear()

    def size(self) -> int:
        now = time.time()
        return sum(1 for _, (_, exp) in self._store.items() if now < exp)


# Instâncias globais por contexto
character_cache = TTLCache()   # TTL 10 min — dados de personagem mudam pouco
item_cache = TTLCache()        # TTL 60 min — dados de item são estáticos
creature_cache = TTLCache()    # TTL 60 min — dados de criatura são estáticos
