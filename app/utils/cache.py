from __future__ import annotations

import inspect
import time
from collections import OrderedDict
from collections.abc import Callable
from functools import wraps
from threading import RLock
from typing import Any, TypeVar

from pydantic import BaseModel

F = TypeVar("F", bound=Callable[..., Any])


def _normalize(value: Any) -> Any:
    """Recursively turn a value into a hashable, order-stable cache-key component."""
    if isinstance(value, BaseModel):
        return _normalize(value.model_dump())
    if isinstance(value, dict):
        return tuple(sorted((k, _normalize(v)) for k, v in value.items()))
    if isinstance(value, (list, tuple, set, frozenset)):
        return tuple(_normalize(v) for v in value)
    return value


def _make_key(
    func: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any],
) -> tuple[Any, ...]:
    bound = inspect.signature(func).bind(*args, **kwargs)
    bound.apply_defaults()
    return tuple(sorted((name, _normalize(v)) for name, v in bound.arguments.items()))


def ttl_cache(
    *,
    maxsize: int = 256,
    ttl_seconds: float = 1800,
    enabled: bool | Callable[[], bool] = True,
) -> Callable[[F], F]:
    """In-process TTL + LRU cache decorator.

    Unlike functools.lru_cache, keys are built by normalizing bound arguments
    (including pydantic BaseModel and list/dict values) into hashable tuples,
    since some callers pass unhashable pydantic models or lists.
    """

    def decorator(func: F) -> F:
        cache: OrderedDict[tuple[Any, ...], tuple[float, Any]] = OrderedDict()
        lock = RLock()

        def _enabled() -> bool:
            if isinstance(enabled, bool):
                return enabled
            return enabled()

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not _enabled():
                return func(*args, **kwargs)

            key = _make_key(func, args, kwargs)
            now = time.monotonic()

            with lock:
                entry = cache.get(key)
                if entry is not None:
                    expires_at, value = entry
                    if expires_at > now:
                        cache.move_to_end(key)
                        return list(value) if isinstance(value, list) else value
                    del cache[key]

            result = func(*args, **kwargs)

            with lock:
                cache[key] = (now + ttl_seconds, result)
                cache.move_to_end(key)
                while len(cache) > maxsize:
                    cache.popitem(last=False)

            return list(result) if isinstance(result, list) else result

        def cache_clear() -> None:
            with lock:
                cache.clear()

        def cache_info() -> dict[str, Any]:
            with lock:
                return {"size": len(cache), "maxsize": maxsize, "ttl_seconds": ttl_seconds}

        wrapper.cache_clear = cache_clear  # type: ignore[attr-defined]
        wrapper.cache_info = cache_info  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    return decorator
