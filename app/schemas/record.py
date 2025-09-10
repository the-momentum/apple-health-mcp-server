from typing import Literal

from pydantic import BaseModel

RecordType = Literal[
    "HKQuantityTypeIdentifierStepCount",
    "HKQuantityTypeIdentifierBodyMassIndex",
    "HKQuantityTypeIdentifierHeartRate",
    "HKQuantityTypeIdentifierBodyMass",
    "HKQuantityTypeIdentifierHeight",
    "HKQuantityTypeIdentifierDietaryWater",
    "HKQuantityTypeIdentifierActiveEnergyBurned",
    "HKQuantityTypeIdentifierBasalEnergyBurned",
    "HKQuantityTypeIdentifierDistanceWalkingRunning",
    "HKQuantityTypeIdentifierRunningSpeed",
    "HKQuantityTypeIdentifierRunningPower",
    "HKQuantityTypeIdentifierAppleExerciseTime",
    "HKQuantityTypeIdentifierAppleStandTime",
    "HKQuantityTypeIdentifierFlightsClimbed",
    "HKQuantityTypeIdentifierWalkingStepLength",
    "HKQuantityTypeIdentifierWalkingSpeed",
    "HKQuantityTypeIdentifierEnvironmentalAudioExposure",
]

IntervalType = Literal["day", "week", "month", "year"]


class HealthRecordSearchParams(BaseModel):
    record_type: RecordType | str | None = None
    source_name: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    value_min: str | None = None
    value_max: str | None = None
    limit: int = 10
