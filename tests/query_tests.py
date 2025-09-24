import os
from pathlib import Path

import pytest

path = Path(__file__).parent / "records.parquet"
os.environ["DUCKDB_FILENAME"] = str(path)

from app.services.health.duckdb_queries import (
    get_health_summary_from_duckdb,
    search_health_records_from_duckdb,
    get_statistics_by_type_from_duckdb,
    get_trend_data_from_duckdb,
    search_values_from_duckdb
)
from app.schemas.record import HealthRecordSearchParams


@pytest.fixture
def counts():
    return {
        'HKQuantityTypeIdentifierBasalEnergyBurned': 18,
        'HKQuantityTypeIdentifierStepCount': 10,
        'HKQuantityTypeIdentifierHeartRate': 17,
        'HKQuantityTypeIdentifierBodyMassIndex': 8,
        'HKQuantityTypeIdentifierDietaryWater': 1,
    }

@pytest.fixture
def summary():
    return get_health_summary_from_duckdb()

@pytest.fixture
def records():
    return search_health_records_from_duckdb(HealthRecordSearchParams(
        record_type="HKQuantityTypeIdentifierStepCount",
        value_min = "65",
        value_max = "90",
    ))

@pytest.fixture
def statistics():
    return get_statistics_by_type_from_duckdb(
        "HKQuantityTypeIdentifierStepCount"
    )

@pytest.fixture
def trend_data():
    return get_trend_data_from_duckdb(
        record_type = "HKQuantityTypeIdentifierBasalEnergyBurned"
    )

@pytest.fixture
def value_search():
    return search_values_from_duckdb(
        record_type = "HKQuantityTypeIdentifierStepCount",
        value = "13"
    )



def test_summary(summary, counts):
    assert len(summary) == 5
    for record in summary:
        assert record['count'] == counts[record['type']]

def test_records(records):
    assert len(records) == 3
    for record in records:
        assert 65 < record['value'] < 90
        assert record['type'] == "HKQuantityTypeIdentifierStepCount"

def test_statistics(statistics):
    assert len(statistics) == 1
    # turn list containing 1 dict into a dict
    statistics = statistics[0]
    assert statistics['min'] == 3
    assert statistics['max'] == 98
    assert statistics['count'] == 10

def test_trend_data(trend_data):
    assert len(trend_data) == 1
    # turn list containing 1 dict into a dict
    trend_data = trend_data[0]
    assert trend_data['min'] == trend_data['max'] == 0.086
    assert trend_data['count'] == 18
    # floating point values not exactly matching
    assert 0.999 < trend_data['sum'] / (18 * 0.086) < 1.001

def test_value_search(value_search):
    assert len(value_search) == 2
    for record in value_search:
        assert record['type'] == "HKQuantityTypeIdentifierStepCount"
