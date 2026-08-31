from collections.abc import Iterator
from pathlib import Path

import pytest

from app.services.health import manual_logs


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

    with pytest.raises(ValueError):
        manual_logs.delete_fueling_event(id="00000000-0000-0000-0000-000000000000")
