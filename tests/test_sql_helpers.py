import pytest

from app.services.health.sql_helpers import get_table, type_filter


def test_get_table_single_type() -> None:
    assert get_table("HKQuantityTypeIdentifierStepCount") == "records"
    assert get_table("HKWorkoutActivityTypeRunning") == "workouts"


def test_get_table_none() -> None:
    assert get_table(None) == "records"


def test_get_table_homogeneous_list() -> None:
    assert get_table(["HKQuantityTypeIdentifierStepCount", "HKQuantityTypeIdentifierHeartRate"]) == "records"
    assert get_table(["HKWorkoutActivityTypeRunning", "HKWorkoutActivityTypeWalking"]) == "workouts"


def test_get_table_mixed_list_raises() -> None:
    with pytest.raises(ValueError, match="mixes"):
        get_table(["HKWorkoutActivityTypeRunning", "HKQuantityTypeIdentifierStepCount"])


def test_type_filter_single() -> None:
    assert type_filter("records", "HKQuantityTypeIdentifierStepCount") == (
        "records.type = 'HKQuantityTypeIdentifierStepCount'"
    )


def test_type_filter_list() -> None:
    assert type_filter("records", ["HKQuantityTypeIdentifierStepCount", "HKQuantityTypeIdentifierHeartRate"]) == (
        "records.type IN ('HKQuantityTypeIdentifierStepCount', 'HKQuantityTypeIdentifierHeartRate')"
    )
