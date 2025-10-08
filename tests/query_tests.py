import os
from pathlib import Path
from typing import Any

import pytest

path = Path(__file__).parent / "duckdb.example"
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
        "HKQuantityTypeIdentifierStepCount": 14,
        "HKQuantityTypeIdentifierHeartRate": 14,
        "HKQuantityTypeIdentifierBasalEnergyBurned": 10,
        "HKQuantityTypeIdentifierDistanceWalkingRunning": 6,
        "HKQuantityTypeIdentifierActiveEnergyBurned": 5,
        "HKQuantityTypeIdentifierBodyMassIndex": 5,
        "HKQuantityTypeIdentifierBodyMass": 5,
        "HKQuantityTypeIdentifierRunningSpeed": 3,
        "HKQuantityTypeIdentifierFlightsClimbed": 3,
        "HKQuantityTypeIdentifierWalkingHeartRateAverage": 2,
        "HKQuantityTypeIdentifierAppleExerciseTime": 2,
        "HKQuantityTypeIdentifierWalkingSpeed": 2,
        "HKQuantityTypeIdentifierRunningStrideLength": 2,
        "HKQuantityTypeIdentifierWalkingDoubleSupportPercentage": 2,
        "HKQuantityTypeIdentifierVO2Max": 2,
        "HKQuantityTypeIdentifierRunningVerticalOscillation": 2,
        "HKQuantityTypeIdentifierOxygenSaturation": 2,
        "HKQuantityTypeIdentifierAppleWalkingSteadiness": 2,
        "HKQuantityTypeIdentifierRunningGroundContactTime": 2,
        "HKQuantityTypeIdentifierRestingHeartRate": 2,
        "HKQuantityTypeIdentifierStairDescentSpeed": 2,
        "HKQuantityTypeIdentifierHeadphoneAudioExposure": 2,
        "HKQuantityTypeIdentifierHeartRateVariabilitySDNN": 2,
        "HKQuantityTypeIdentifierWalkingStepLength": 2,
        "HKQuantityTypeIdentifierAppleStandTime": 2,
        "HKQuantityTypeIdentifierWalkingAsymmetryPercentage": 2,
        "HKQuantityTypeIdentifierRunningPower": 2,
        "HKQuantityTypeIdentifierEnvironmentalAudioExposure": 2,
        "HKQuantityTypeIdentifierStairAscentSpeed": 2,
        "HKQuantityTypeIdentifierRespiratoryRate": 2,
        "HKQuantityTypeIdentifierHeight": 1,
        "HKWorkoutActivityTypeRunning": 24,
        "HKWorkoutActivityTypeWalking": 5,
        "HKWorkoutActivityTypeHiking": 3,
        "HKWorkoutActivityTypeCycling": 3,
        "HKWorkoutActivityTypeMixedMetabolicCardioTraining": 2,
        "HKWorkoutActivityTypeHockey": 2,
        "HKWorkoutActivityTypeHighIntensityIntervalTraining": 2,
        "HKWorkoutActivityTypeTraditionalStrengthTraining": 2
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
def workouts() -> list[dict[str, Any]]:
    return search_health_records_from_duckdb(
        HealthRecordSearchParams(
            limit=20,
            record_type="HKWorkoutActivityTypeRunning",
            min_workout_duration="45",
            max_workout_duration="53"
        )
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
        interval="year"
    )


@pytest.fixture
def value_search() -> list[dict[str, Any]]:
    return search_values_from_duckdb(
        record_type="HKQuantityTypeIdentifierStepCount",
        value="13",
    )


def test_summary(summary: list[dict[str, Any]], counts: dict[str, int]) -> None:
    assert len(summary) == len(counts)
    for record in summary:
        assert record["count"] == counts[record["type"]]


def test_records(records: list[dict[str, Any]]) -> None:
    assert len(records) == 2
    for record in records:
        assert 65 < record["value"] < 90
        assert record["type"] == "HKQuantityTypeIdentifierStepCount"

def test_workouts(workouts: list[dict[str, Any]]) -> None:
    # 3 records, however there are 20 total stats associated with them
    assert len(workouts) == 20
    for record in workouts:
        assert 30 < record["duration"] < 60
        assert record["type"] == "HKWorkoutActivityTypeRunning"



def test_statistics(statistics: list[dict[str, Any]] | dict[str, Any]) -> None:
    assert len(statistics) == 1
    # turn list containing 1 dict into a dict
    stats: dict[str, Any] = statistics[0]
    assert stats["min"] == 13
    assert stats["max"] == 4567
    assert stats["count"] == 14


def test_trend_data(trend_data: list[dict[str, Any]] | dict[str, Any]) -> None:
    assert len(trend_data) == 2
    # turn list containing 1 dict into a dict
    data: dict[str, Any] = trend_data[0]
    assert data["count"] == 5
    assert data["min"] == 0.086
    assert data["max"] == 0.086
    # floating point values not exactly matching
    assert 0.999 < data["sum"] / (0.086 * 5) < 1.001


def test_value_search(value_search: list[dict[str, Any]]) -> None:
    assert len(value_search) == 2
    for record in value_search:
        assert record["type"] == "HKQuantityTypeIdentifierStepCount"
