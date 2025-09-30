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

WorkoutType = Literal[
    "HKWorkoutActivityTypeRunning",
    "HKWorkoutActivityTypeWalking",
    "HKWorkoutActivityTypeHiking",
    "HKWorkoutActivityTypeTraditionalStrengthTraining",
    "HKWorkoutActivityTypeCycling",
    "HKWorkoutActivityTypeMixedMetabolicCardioTraining",
    "HKWorkoutActivityTypeHighIntensityIntervalTraining",
    "HKWorkoutActivityTypeHockey",
]

IntervalType = Literal["day", "week", "month", "year"]


class HealthRecordSearchParams(BaseModel):
    record_type: RecordType | WorkoutType | str | None = None
    source_name: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    min_workout_duration: str | None = None
    max_workout_duration: str | None = None
    value_min: str | None = None
    value_max: str | None = None
    limit: int = 10
