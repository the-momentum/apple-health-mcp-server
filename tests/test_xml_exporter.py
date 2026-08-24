import io

from scripts.xml_exporter import XMLExporter

SAMPLE_XML = b"""<HealthData>
<Workout workoutActivityType="HKWorkoutActivityTypeWalking" duration="30"
    durationUnit="min" sourceName="iPhone"
    startDate="2026-01-01 00:00:00 +0000" endDate="2026-01-01 00:30:00 +0000">
<WorkoutStatistics type="HKQuantityTypeIdentifierActiveEnergyBurned"
    startDate="2026-01-01 00:00:00 +0000" endDate="2026-01-01 00:30:00 +0000"
    sum="100" unit="kcal"/>
<WorkoutStatistics type="HKQuantityTypeIdentifierDistanceWalkingRunning"
    startDate="2026-01-01 00:00:00 +0000" endDate="2026-01-01 00:30:00 +0000"
    sum="2.5" unit="km"/>
</Workout>
</HealthData>"""


def test_workout_statistics_are_captured_not_cleared() -> None:
    exporter = XMLExporter.__new__(XMLExporter)
    exporter.chunk_size = 50000
    exporter.cutoff_date = None

    frames = list(exporter.parse_xml(source=io.BytesIO(SAMPLE_XML)))
    stats = next(df for df in frames if set(df.columns) == set(exporter.WORKOUT_STATS_COLUMNS))

    assert len(stats) == 2
    assert stats["type"].notna().all()
    assert stats["startDate"].notna().all()
    assert set(stats["sum"]) == {100.0, 2.5}
