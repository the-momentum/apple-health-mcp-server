import time

from pydantic import BaseModel

from app.utils.cache import ttl_cache


def test_ttl_cache_hits_avoid_recompute() -> None:
    calls = {"n": 0}

    @ttl_cache(maxsize=10, ttl_seconds=60)
    def fn(a: int, b: str | None = None) -> int:
        calls["n"] += 1
        return a

    assert fn(1) == 1
    assert fn(1) == 1
    assert calls["n"] == 1


def test_ttl_cache_respects_ttl_expiry() -> None:
    calls = {"n": 0}

    @ttl_cache(maxsize=10, ttl_seconds=0.01)
    def fn(a: int) -> int:
        calls["n"] += 1
        return a

    assert fn(1) == 1
    time.sleep(0.02)
    assert fn(1) == 1
    assert calls["n"] == 2


def test_ttl_cache_evicts_lru_beyond_maxsize() -> None:
    calls = {"n": 0}

    @ttl_cache(maxsize=2, ttl_seconds=60)
    def fn(a: int) -> int:
        calls["n"] += 1
        return a

    fn(1)
    fn(2)
    fn(3)  # evicts 1
    assert calls["n"] == 3

    fn(1)  # recomputed, since it was evicted
    assert calls["n"] == 4

    fn(3)  # still cached
    assert calls["n"] == 4


def test_ttl_cache_disabled_bypasses_cache() -> None:
    calls = {"n": 0}

    @ttl_cache(maxsize=10, ttl_seconds=60, enabled=False)
    def fn(a: int) -> int:
        calls["n"] += 1
        return a

    fn(1)
    fn(1)
    assert calls["n"] == 2


def test_ttl_cache_disabled_via_callable() -> None:
    calls = {"n": 0}
    flag = {"enabled": True}

    @ttl_cache(maxsize=10, ttl_seconds=60, enabled=lambda: flag["enabled"])
    def fn(a: int) -> int:
        calls["n"] += 1
        return a

    fn(1)
    fn(1)
    assert calls["n"] == 1

    flag["enabled"] = False
    fn(1)
    assert calls["n"] == 2


class _Params(BaseModel):
    record_type: str
    limit: int = 10


def test_ttl_cache_normalizes_basemodel_and_list_args() -> None:
    calls = {"n": 0}

    @ttl_cache(maxsize=10, ttl_seconds=60)
    def fn(params: _Params, types: list[str]) -> str:
        calls["n"] += 1
        return params.record_type

    fn(_Params(record_type="HR"), ["a", "b"])
    fn(_Params(record_type="HR"), ["a", "b"])
    assert calls["n"] == 1

    fn(_Params(record_type="HR"), ["a", "c"])
    assert calls["n"] == 2


def test_ttl_cache_returns_independent_list_on_hit() -> None:
    @ttl_cache(maxsize=10, ttl_seconds=60)
    def fn() -> list[int]:
        return [1, 2, 3]

    first = fn()
    first.append(4)

    second = fn()
    assert second == [1, 2, 3]
