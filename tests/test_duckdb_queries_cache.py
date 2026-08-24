from collections.abc import Iterator

import pytest

from app.config import settings
from app.schemas.record import HealthRecordSearchParams
from app.services.health import duckdb_queries

DATE_FROM = "2026-01-01"


class _FakeDF:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def to_dict(self, orient: str = "records") -> list[dict]:
        return list(self._rows)


class _FakeRelation:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def df(self) -> _FakeDF:
        return _FakeDF(self._rows)

    def __iter__(self):
        return iter([self])


class _FakeConnection:
    def __init__(self) -> None:
        self.calls = 0

    def sql(self, _query: str, *, params: dict | None = None) -> _FakeRelation:
        self.calls += 1
        return _FakeRelation([{"type": "x", "count": self.calls}])


FUNCS = [
    duckdb_queries.get_health_summary_from_duckdb,
    duckdb_queries.search_health_records_from_duckdb,
    duckdb_queries.get_statistics_by_type_from_duckdb,
    duckdb_queries.get_trend_data_from_duckdb,
    duckdb_queries.get_sleep_summary_from_duckdb,
    duckdb_queries.search_values_from_duckdb,
]


@pytest.fixture(autouse=True)
def duckdb_connection(monkeypatch: pytest.MonkeyPatch) -> Iterator[_FakeConnection]:
    for fn in FUNCS:
        fn.cache_clear()
    monkeypatch.setattr(settings, "DUCKDB_QUERY_CACHE_ENABLED", True)
    fake_con = _FakeConnection()
    monkeypatch.setattr(duckdb_queries, "_get_con", lambda: fake_con)
    yield fake_con
    for fn in FUNCS:
        fn.cache_clear()


def test_get_health_summary_is_cached(duckdb_connection: _FakeConnection) -> None:
    duckdb_queries.get_health_summary_from_duckdb()
    duckdb_queries.get_health_summary_from_duckdb()
    assert duckdb_connection.calls == 2  # one call issues 2 .sql() calls (records + workouts)


def test_get_trend_data_is_cached(duckdb_connection: _FakeConnection) -> None:
    record_type = "HKQuantityTypeIdentifierStepCount"
    duckdb_queries.get_trend_data_from_duckdb(record_type, date_from=DATE_FROM)
    calls_after_first = duckdb_connection.calls
    duckdb_queries.get_trend_data_from_duckdb(record_type, date_from=DATE_FROM)
    assert duckdb_connection.calls == calls_after_first


def test_get_statistics_by_type_is_cached(duckdb_connection: _FakeConnection) -> None:
    record_type = "HKQuantityTypeIdentifierStepCount"
    duckdb_queries.get_statistics_by_type_from_duckdb(record_type)
    calls_after_first = duckdb_connection.calls
    duckdb_queries.get_statistics_by_type_from_duckdb(record_type)
    assert duckdb_connection.calls == calls_after_first


def test_search_health_records_is_cached(duckdb_connection: _FakeConnection) -> None:
    record_type = "HKQuantityTypeIdentifierStepCount"
    duckdb_queries.search_health_records_from_duckdb(
        HealthRecordSearchParams(record_type=record_type, limit=5),
    )
    calls_after_first = duckdb_connection.calls
    duckdb_queries.search_health_records_from_duckdb(
        HealthRecordSearchParams(record_type=record_type, limit=5),
    )
    assert duckdb_connection.calls == calls_after_first


def test_disabled_setting_bypasses_cache(
    monkeypatch: pytest.MonkeyPatch, duckdb_connection: _FakeConnection,
) -> None:
    monkeypatch.setattr(settings, "DUCKDB_QUERY_CACHE_ENABLED", False)
    record_type = "HKQuantityTypeIdentifierStepCount"
    duckdb_queries.get_statistics_by_type_from_duckdb(record_type)
    calls_after_first = duckdb_connection.calls
    duckdb_queries.get_statistics_by_type_from_duckdb(record_type)
    assert duckdb_connection.calls > calls_after_first


def test_cache_clear_forces_recompute(duckdb_connection: _FakeConnection) -> None:
    record_type = "HKQuantityTypeIdentifierStepCount"
    duckdb_queries.get_statistics_by_type_from_duckdb(record_type)
    calls_after_first = duckdb_connection.calls
    duckdb_queries.get_statistics_by_type_from_duckdb.cache_clear()
    duckdb_queries.get_statistics_by_type_from_duckdb(record_type)
    assert duckdb_connection.calls > calls_after_first
