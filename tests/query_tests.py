import os
from pathlib import Path
from typing import Any

import pytest

path = Path(__file__).parent / "parquet_example"
os.environ["DUCKDB_FILENAME"] = str(path)

from app.schemas.record import HealthRecordSearchParams
from app.services.health.duckdb_queries import (
    get_health_summary_from_duckdb,
    get_statistics_by_type_from_duckdb,
    get_trend_data_from_duckdb,
    search_health_records_from_duckdb,
    search_values_from_duckdb,
)


@pytest.fixture
def counts() -> dict[str, int]:
    return {
        "HKQuantityTypeIdentifierBasalEnergyBurned": 18,
        "HKQuantityTypeIdentifierStepCount": 10,
        "HKQuantityTypeIdentifierHeartRate": 17,
        "HKQuantityTypeIdentifierBodyMassIndex": 8,
        "HKQuantityTypeIdentifierDietaryWater": 1,
    }


@pytest.fixture
def summary() -> list[dict[str, Any]]:
    return get_health_summary_from_duckdb()


@pytest.fixture
def records() -> list[dict[str, Any]]:
    return search_health_records_from_duckdb(
        HealthRecordSearchParams(
            record_type="HKQuantityTypeIdentifierStepCount",
            value_min="65",
            value_max="90",
        ),
    )


@pytest.fixture
def statistics() -> list[dict[str, Any]]:
    return get_statistics_by_type_from_duckdb(
        "HKQuantityTypeIdentifierStepCount",
    )


@pytest.fixture
def trend_data() -> list[dict[str, Any]]:
    return get_trend_data_from_duckdb(
        record_type="HKQuantityTypeIdentifierBasalEnergyBurned",
    )


@pytest.fixture
def value_search() -> list[dict[str, Any]]:
    return search_values_from_duckdb(
        record_type="HKQuantityTypeIdentifierStepCount",
        value="13",
    )


def test_summary(summary: list[dict[str, Any]], counts: dict[str, int]) -> None:
    assert len(summary) == 5
    for record in summary:
        assert record["count"] == counts[record["type"]]


def test_records(records: list[dict[str, Any]]) -> None:
    assert len(records) == 3
    for record in records:
        assert 65 < record["value"] < 90
        assert record["type"] == "HKQuantityTypeIdentifierStepCount"


def test_statistics(statistics: list[dict[str, Any]] | dict[str, Any]) -> None:
    assert len(statistics) == 1
    # turn list containing 1 dict into a dict
    stats: dict[str, Any] = statistics[0]
    assert stats["min"] == 3
    assert stats["max"] == 98
    assert stats["count"] == 10


def test_trend_data(trend_data: list[dict[str, Any]]) -> None:
    assert len(trend_data) == 1
    # turn list containing 1 dict into a dict
    data: dict[str, Any] = trend_data[0]
    assert data["min"] == data["max"] == 0.086
    assert data["count"] == 18
    # floating point values not exactly matching
    assert 0.999 < data["sum"] / (18 * 0.086) < 1.001


def test_value_search(value_search: list[dict[str, Any]]) -> None:
    assert len(value_search) == 2
    for record in value_search:
        assert record["type"] == "HKQuantityTypeIdentifierStepCount"
