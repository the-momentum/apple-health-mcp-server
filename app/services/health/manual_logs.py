import atexit
import json
import os
import sys
import threading
from pathlib import Path
from typing import Any

import duckdb

from app.config import settings
from app.schemas.manual_log import FuelingCategory
from app.services.duckdb_client import DuckDBClient

client = DuckDBClient(path=settings.LOGS_DUCKDB_FILENAME)
_con: duckdb.DuckDBPyConnection | None = None
_lock = threading.Lock()

FUELING_EVENTS_SCHEMA = """
    CREATE TABLE IF NOT EXISTS fueling_events (
        id UUID DEFAULT gen_random_uuid(),
        logged_at TIMESTAMP,
        category VARCHAR,
        product_name VARCHAR,
        brand VARCHAR,
        quantity VARCHAR,
        shop_url VARCHAR,
        calories DOUBLE,
        carbs_g DOUBLE,
        sodium_mg DOUBLE,
        caffeine_mg DOUBLE,
        notes VARCHAR,
        created_at TIMESTAMP DEFAULT now()
    );
"""


def _get_con() -> duckdb.DuckDBPyConnection:
    global _con
    if _con is None:
        _con = duckdb.connect(str(client.path))
        _con.sql(FUELING_EVENTS_SCHEMA)
    return _con


def _json_mirror_path() -> Path:
    """Sibling of the DB file, e.g. data/manual_logs.fueling_events.json."""
    return Path(str(client.path)).with_name("manual_logs.fueling_events.json")


def _write_json_mirror(con: duckdb.DuckDBPyConnection) -> None:
    """
    Dump the whole fueling_events table to a human-readable, diffable JSON file
    next to the DB. Written atomically (tmp + os.replace). A failure here must
    never fail the logging operation, so callers are shielded by try/except.
    """
    # Read rows directly (not via .df()): SQL NULL comes back as None, so the
    # output is always strict, valid JSON. Going through pandas would turn NULL
    # DOUBLEs into NaN and emit invalid `NaN` tokens.
    cur = con.execute("SELECT * FROM fueling_events ORDER BY logged_at")
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r, strict=True)) for r in cur.fetchall()]
    path = _json_mirror_path()
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(rows, indent=2, default=str, allow_nan=False))
    os.replace(tmp, path)


def _persist(con: duckdb.DuckDBPyConnection) -> None:
    """
    Make the last write durable immediately: fold the WAL into the main .duckdb
    file so the data survives the process being killed, then refresh the JSON
    mirror. Manual-log volume is tiny and writes are rare, so the per-write
    CHECKPOINT cost is negligible.
    """
    con.execute("CHECKPOINT")
    try:
        _write_json_mirror(con)
    except Exception as e:  # noqa: BLE001 - mirror is best-effort
        print(f"manual_logs: failed to write JSON mirror: {e}", file=sys.stderr)


def close_con() -> None:
    """Checkpoint and close the module connection (graceful shutdown / atexit)."""
    global _con
    with _lock:
        if _con is not None:
            try:
                _con.execute("CHECKPOINT")
            finally:
                _con.close()
                _con = None


atexit.register(close_con)


def log_fueling_event(
    product_name: str,
    category: FuelingCategory,
    brand: str | None = None,
    quantity: str | None = None,
    shop_url: str | None = None,
    calories: float | None = None,
    carbs_g: float | None = None,
    sodium_mg: float | None = None,
    caffeine_mg: float | None = None,
    notes: str | None = None,
    logged_at: str | None = None,
) -> dict[str, Any]:
    with _lock:
        con = _get_con()
        result = con.execute(
            """
            INSERT INTO fueling_events (
                logged_at, category, product_name, brand, quantity, shop_url,
                calories, carbs_g, sodium_mg, caffeine_mg, notes
            ) VALUES (
                COALESCE(?::TIMESTAMP, now()), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            RETURNING *
            """,
            [
                logged_at,
                category,
                product_name,
                brand,
                quantity,
                shop_url,
                calories,
                carbs_g,
                sodium_mg,
                caffeine_mg,
                notes,
            ],
        )
        rows = result.df().to_dict(orient="records")
        _persist(con)
        return rows[0]


def delete_fueling_event(id: str) -> dict[str, Any]:
    with _lock:
        con = _get_con()
        result = con.execute(
            "DELETE FROM fueling_events WHERE id = ?::UUID RETURNING *",
            [id],
        )
        rows = result.df().to_dict(orient="records")
        if not rows:
            raise ValueError(f"No fueling event found with id={id}")
        _persist(con)
    return rows[0]


def search_fueling_events(
    date_from: str | None = None,
    date_to: str | None = None,
    category: FuelingCategory | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    with _lock:
        con = _get_con()
        query = "SELECT * FROM fueling_events WHERE 1=1"
        params: list[Any] = []
        if date_from:
            query += " AND logged_at >= ?::TIMESTAMP"
            params.append(date_from)
        if date_to:
            query += " AND logged_at <= ?::TIMESTAMP"
            params.append(date_to)
        if category:
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY logged_at DESC LIMIT ?"
        params.append(limit)

        result = con.execute(query, params)
        return result.df().to_dict(orient="records")
