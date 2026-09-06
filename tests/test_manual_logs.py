import json
import shutil
from collections.abc import Iterator
from pathlib import Path

import duckdb
import pytest

from app.services.health import manual_logs


def _rows_without_wal(db_path: Path, tmp_path: Path) -> list[tuple]:
    """Copy only the main .duckdb file (no .wal) and read it back — proves the
    data was checkpointed into the main file and does not depend on the WAL."""
    isolated = tmp_path / "no_wal_copy.duckdb"
    shutil.copy(db_path, isolated)
    con = duckdb.connect(str(isolated), read_only=True)
    try:
        return con.execute("SELECT product_name FROM fueling_events").fetchall()
    finally:
        con.close()


@pytest.fixture(autouse=True)
def temp_logs_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    db_path = tmp_path / "manual_logs.duckdb"
    monkeypatch.setattr(manual_logs.client, "path", db_path)
    manual_logs._con = None
    yield db_path
    if manual_logs._con is not None:
        manual_logs._con.close()
    manual_logs._con = None


def test_log_fueling_event_creates_table_and_row() -> None:
    row = manual_logs.log_fueling_event(
        product_name="Maurten Gel 100",
        category="gel",
        brand="Maurten",
    )
    assert row["product_name"] == "Maurten Gel 100"
    assert row["category"] == "gel"
    assert row["brand"] == "Maurten"
    assert row["id"] is not None


def test_search_fueling_events_returns_logged_event() -> None:
    manual_logs.log_fueling_event(product_name="Tailwind", category="drink_mix")

    results = manual_logs.search_fueling_events()

    assert len(results) == 1
    assert results[0]["product_name"] == "Tailwind"


def test_search_fueling_events_filters_by_category() -> None:
    manual_logs.log_fueling_event(product_name="Tailwind", category="drink_mix")
    manual_logs.log_fueling_event(product_name="Clif Bar", category="bar")

    results = manual_logs.search_fueling_events(category="bar")

    assert len(results) == 1
    assert results[0]["product_name"] == "Clif Bar"


def test_search_fueling_events_filters_by_date_range() -> None:
    manual_logs.log_fueling_event(
        product_name="Old Gel",
        category="gel",
        logged_at="2020-01-01T10:00:00",
    )
    manual_logs.log_fueling_event(
        product_name="Recent Gel",
        category="gel",
        logged_at="2026-01-01T10:00:00",
    )

    results = manual_logs.search_fueling_events(date_from="2025-01-01")

    assert len(results) == 1
    assert results[0]["product_name"] == "Recent Gel"


def test_logged_at_defaults_to_now_when_not_given() -> None:
    row = manual_logs.log_fueling_event(product_name="Gel", category="gel")

    assert row["logged_at"] is not None


def test_delete_fueling_event_removes_row() -> None:
    logged = manual_logs.log_fueling_event(product_name="Wrong Gel", category="gel")
    manual_logs.log_fueling_event(product_name="Correct Gel", category="gel")

    deleted = manual_logs.delete_fueling_event(id=str(logged["id"]))

    assert deleted["product_name"] == "Wrong Gel"
    results = manual_logs.search_fueling_events()
    assert len(results) == 1
    assert results[0]["product_name"] == "Correct Gel"


def test_delete_fueling_event_unknown_id_raises() -> None:
    manual_logs.log_fueling_event(product_name="Gel", category="gel")

    with pytest.raises(ValueError, match="No fueling event found"):
        manual_logs.delete_fueling_event(id="00000000-0000-0000-0000-000000000000")


def test_log_fueling_event_is_durable_without_wal(
    temp_logs_db: Path, tmp_path: Path,
) -> None:
    manual_logs.log_fueling_event(product_name="Durable Gel", category="gel")

    assert _rows_without_wal(temp_logs_db, tmp_path) == [("Durable Gel",)]


def test_delete_is_durable_without_wal(temp_logs_db: Path, tmp_path: Path) -> None:
    keep = manual_logs.log_fueling_event(product_name="Keep", category="gel")  # noqa: F841
    drop = manual_logs.log_fueling_event(product_name="Drop", category="gel")

    manual_logs.delete_fueling_event(id=str(drop["id"]))

    assert _rows_without_wal(temp_logs_db, tmp_path) == [("Keep",)]


def test_writes_json_mirror(temp_logs_db: Path) -> None:
    manual_logs.log_fueling_event(
        product_name="Mirror Gel", category="gel", brand="Maurten",
    )

    mirror = temp_logs_db.with_name("manual_logs.fueling_events.json")
    assert mirror.exists()
    data = json.loads(mirror.read_text())
    assert [r["product_name"] for r in data] == ["Mirror Gel"]
    assert data[0]["brand"] == "Maurten"


def _reject_nan(value: str) -> None:
    raise AssertionError(f"mirror is not strict JSON: contains {value}")


def test_json_mirror_is_strict_json_with_null_not_nan(temp_logs_db: Path) -> None:
    # Numeric fields left unset must serialize as JSON null, not a `NaN` token
    # (which strict parsers like JS JSON.parse / jq reject).
    manual_logs.log_fueling_event(
        product_name="No Nutrition Gel", category="gel", calories=None,
    )

    mirror = temp_logs_db.with_name("manual_logs.fueling_events.json")
    text = mirror.read_text()
    assert "NaN" not in text
    data = json.loads(text, parse_constant=_reject_nan)
    assert data[0]["calories"] is None
    assert data[0]["caffeine_mg"] is None


def test_json_mirror_reflects_deletes(temp_logs_db: Path) -> None:
    manual_logs.log_fueling_event(product_name="Stays", category="gel")
    gone = manual_logs.log_fueling_event(product_name="Goes", category="gel")

    manual_logs.delete_fueling_event(id=str(gone["id"]))

    mirror = temp_logs_db.with_name("manual_logs.fueling_events.json")
    data = json.loads(mirror.read_text())
    assert [r["product_name"] for r in data] == ["Stays"]


def test_close_con_checkpoints_and_resets(temp_logs_db: Path, tmp_path: Path) -> None:
    manual_logs.log_fueling_event(product_name="Flushed", category="gel")

    manual_logs.close_con()

    assert manual_logs._con is None
    assert _rows_without_wal(temp_logs_db, tmp_path) == [("Flushed",)]
