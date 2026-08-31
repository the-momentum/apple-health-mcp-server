"""
Tests for scripts/duckdb_importer.py — the atomic-rebuild import pipeline.

Serial tests drive ParquetImporter.export_xml for deterministic, single-process
assertions and rely on `imp.cutoff_date = None` to neutralize
IMPORT_LOOKBACK_MONTHS. The parallel test spawns worker processes that rebuild
`settings` from scratch, so it must widen the lookback via
`monkeypatch.setenv("IMPORT_LOOKBACK_MONTHS", ...)` — `monkeypatch.setattr` on the
settings object does not reach subprocesses.
"""

from collections.abc import Callable
from pathlib import Path

import duckdb
import pytest

from app.config import settings
from scripts import duckdb_importer
from scripts.duckdb_importer import ParquetImporter

RECENT = "2026-08-15 08:00:00 +0000"


def _record(
    *,
    value: str = "1",
    device: str = "iPhone10,3",
    source_version: str = "1.0",
    start: str = RECENT,
) -> str:
    return (
        '<Record type="HKQuantityTypeIdentifierStepCount" sourceName="iPhone" '
        f'sourceVersion="{source_version}" device="{device}" unit="count" '
        f'value="{value}" startDate="{start}" endDate="{start}" creationDate="{start}"/>'
    )


_WORKOUT = (
    '<Workout workoutActivityType="HKWorkoutActivityTypeWalking" duration="30" '
    f'durationUnit="min" sourceName="iPhone" startDate="{RECENT}" endDate="{RECENT}" '
    f'creationDate="{RECENT}">'
    f'<WorkoutStatistics type="HKQuantityTypeIdentifierActiveEnergyBurned" '
    f'startDate="{RECENT}" endDate="{RECENT}" sum="100" unit="kcal"/>'
    f'<WorkoutStatistics type="HKQuantityTypeIdentifierDistanceWalkingRunning" '
    f'startDate="{RECENT}" endDate="{RECENT}" sum="2.5" unit="km"/>'
    "</Workout>"
)


def _xml(*elements: str) -> bytes:
    body = "\n".join(f" {el}" for el in elements)
    return f"<HealthData>\n{body}\n</HealthData>".encode()


def _counts(db_path: Path) -> dict[str, int]:
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        return {
            t: con.sql(f"SELECT count(*) FROM {t}").fetchone()[0]
            for t in ("records", "workouts", "stats")
        }
    finally:
        con.close()


@pytest.fixture
def make_importer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Callable[..., ParquetImporter]:
    def _make(xml_bytes: bytes = b"<HealthData>\n</HealthData>") -> ParquetImporter:
        xml_file = tmp_path / "export.xml"
        xml_file.write_bytes(xml_bytes)
        imp = ParquetImporter()
        monkeypatch.setattr(imp, "xml_path", xml_file)
        monkeypatch.setattr(imp, "path", tmp_path / "applehealth.duckdb")
        imp.cutoff_date = None  # neutralize IMPORT_LOOKBACK_MONTHS for serial runs
        return imp

    return _make


def _no_staging_files(directory: Path) -> bool:
    return list(directory.glob("*.import-*.tmp*")) == []


def test_import_is_idempotent(make_importer: Callable[..., ParquetImporter], tmp_path: Path) -> None:
    imp = make_importer(_xml(_record(value="1"), _record(value="2"), _WORKOUT))

    imp.export_xml()
    first = _counts(imp.path)
    imp.export_xml()
    second = _counts(imp.path)

    assert first == {"records": 2, "workouts": 1, "stats": 2}
    assert second == first
    assert _no_staging_files(tmp_path)


def test_builds_fresh_db_with_no_wal_left(make_importer: Callable[..., ParquetImporter]) -> None:
    imp = make_importer(_xml(_record(), _WORKOUT))
    assert not imp.path.exists()

    imp.export_xml()

    assert imp.path.exists()
    assert not Path(f"{imp.path}.wal").exists()
    assert not Path(f"{imp.path}-wal").exists()
    assert _counts(imp.path) == {"records": 1, "workouts": 1, "stats": 2}


def test_failed_swap_leaves_live_db_intact(
    make_importer: Callable[..., ParquetImporter],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    imp = make_importer(_xml(_record(value="1"), _record(value="2")))
    imp.export_xml()
    before = _counts(imp.path)

    def _boom(*_args: object, **_kwargs: object) -> None:
        raise OSError("swap failed")

    monkeypatch.setattr(duckdb_importer.os, "replace", _boom)
    imp2 = make_importer(_xml(_record(value="9")))
    with pytest.raises(OSError, match="swap failed"):
        imp2.export_xml()

    assert _counts(imp.path) == before
    assert _no_staging_files(tmp_path)


def test_failure_during_schema_setup_cleans_up(
    make_importer: Callable[..., ParquetImporter],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    imp = make_importer(_xml(_record(value="1")))
    imp.export_xml()
    before = _counts(imp.path)

    monkeypatch.setattr(duckdb_importer, "WORKOUTS_SCHEMA", "CREATE TABLE workouts (bad")
    imp2 = make_importer(_xml(_record(value="2")))
    with pytest.raises(duckdb.Error):
        imp2.export_xml()

    assert _counts(imp.path) == before
    assert _no_staging_files(tmp_path)


@pytest.mark.parametrize("spelling", ["data/manual_logs.duckdb", "./data/manual_logs.duckdb"])
def test_refuses_to_target_logs_db(
    make_importer: Callable[..., ParquetImporter],
    monkeypatch: pytest.MonkeyPatch,
    spelling: str,
) -> None:
    assert settings.LOGS_DUCKDB_FILENAME == "data/manual_logs.duckdb"
    logs_db = Path(spelling)
    mtime_before = logs_db.stat().st_mtime_ns if logs_db.exists() else None

    imp = make_importer(_xml(_record()))
    monkeypatch.setattr(imp, "path", logs_db)
    with pytest.raises(RuntimeError, match="manual-logs"):
        imp.export_xml()

    if mtime_before is not None:
        assert logs_db.stat().st_mtime_ns == mtime_before


def test_reset_removes_import_db_only(make_importer: Callable[..., ParquetImporter], tmp_path: Path) -> None:
    imp = make_importer(_xml(_record()))
    imp.export_xml()
    assert imp.path.exists()

    # simulate an orphaned staging file from a killed run
    orphan = tmp_path / "applehealth.duckdb.import-99999.tmp"
    orphan.write_bytes(b"stale")

    duckdb_importer._remove_db_files(imp.path)
    duckdb_importer._sweep_orphans(imp.path)

    assert not imp.path.exists()
    assert not orphan.exists()


def test_parallel_import_is_idempotent(
    make_importer: Callable[..., ParquetImporter],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Widen lookback via env so the spawned worker (which rebuilds settings) keeps
    # the RECENT-dated rows regardless of the repo's config/.env value.
    monkeypatch.setenv("IMPORT_LOOKBACK_MONTHS", "1200")
    imp = make_importer(_xml(_record(value="1"), _record(value="2"), _WORKOUT))

    imp.export_xml_parallel(workers=1)
    first = _counts(imp.path)
    imp.export_xml_parallel(workers=1)
    second = _counts(imp.path)

    assert first == {"records": 2, "workouts": 1, "stats": 2}
    assert second == first
    assert _no_staging_files(tmp_path)
