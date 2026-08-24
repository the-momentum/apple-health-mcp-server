import logging
from typing import Any

import duckdb

from app.config import settings
from app.schemas.record import (
    HealthRecordSearchParams,
    IntervalType,
    RecordType,
    WorkoutType,
)
from app.services.duckdb_client import DuckDBClient
from app.services.health.sql_helpers import (
    fill_query,
    get_table,
    join_query,
    join_string,
    type_filter,
    value_aggregates,
)
from app.utils.cache import ttl_cache

client = DuckDBClient()
_con = None


def _cache_enabled() -> bool:
    return settings.DUCKDB_QUERY_CACHE_ENABLED


_default_cache = {
    "maxsize": settings.DUCKDB_QUERY_CACHE_MAXSIZE,
    "ttl_seconds": settings.DUCKDB_QUERY_CACHE_TTL_SECONDS,
    "enabled": _cache_enabled,
}


def _get_con() -> duckdb.DuckDBPyConnection:
    global _con
    if _con is None:
        _con = duckdb.connect(client.path, read_only=True)
    return _con


@ttl_cache(**_default_cache)
def get_health_summary_from_duckdb() -> list[dict[str, Any]]:
    records = _get_con().sql(
        """SELECT type, COUNT(*) AS count FROM records
        GROUP BY type ORDER BY count DESC""",
    )
    workouts = _get_con().sql(
        f"""SELECT workouts.type, COUNT(*) AS count FROM workouts {join_query}
        GROUP BY workouts.type ORDER BY count DESC""",
    )

    return client.format_response([records, workouts])


@ttl_cache(**_default_cache)
def search_health_records_from_duckdb(
    params: HealthRecordSearchParams,
) -> list[dict[str, Any]]:
    query: str = "SELECT * FROM"
    query += fill_query(params)
    response = _get_con().sql(query)
    return client.format_response(response)


@ttl_cache(**_default_cache)
def get_statistics_by_type_from_duckdb(
    record_type: RecordType | WorkoutType | list[str] | str,
    source_name: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    table = get_table(record_type)
    complimentary_table = "stats" if table == "workouts" else "records"
    join_clause = join_string(table)
    values = value_aggregates(table)
    results = []

    query_params: dict[str, Any] = {}
    if source_name:
        query_params["source_name"] = source_name
    if date_from:
        query_params["date_from"] = date_from
    if date_to:
        query_params["date_to"] = date_to

    value = values[0]
    for value in values:
        results.append(
            _get_con().sql(
                f"""
                    SELECT {table}.type, {complimentary_table}.type AS stat_type, COUNT(*) AS count,
                    AVG({value}) AS average, SUM({value}) AS sum, MIN({value}) AS min,
                    MAX({value}) AS max, unit FROM {table} {join_clause}
                    WHERE {type_filter(table, record_type)}
                    {"AND sourceName = $source_name" if source_name else ""}
                    {f"AND {table}.startDate >= $date_from" if date_from else ""}
                    {f"AND {table}.startDate <= $date_to" if date_to else ""}
                    GROUP BY {table}.type,
                    {complimentary_table}.type, unit
                    """,
                params=query_params,
            ),
        )
    return client.format_response(results)


@ttl_cache(**_default_cache)
def get_trend_data_from_duckdb(
    record_type: RecordType | WorkoutType | list[str] | str,
    interval: IntervalType = "month",
    date_from: str | None = None,
    date_to: str | None = None,
    source_name: str | None = None,
) -> list[dict[str, Any]]:
    table = get_table(record_type)
    join_clause = join_string(table)
    values = value_aggregates(table)
    results = []

    query_params: dict[str, Any] = {}
    if source_name:
        query_params["source_name"] = source_name
    if date_from:
        query_params["date_from"] = date_from
    if date_to:
        query_params["date_to"] = date_to

    for value in values:
        results.append(
            _get_con().sql(
                f"""
            SELECT {table}.type, sourceName, time_bucket(INTERVAL '1 {interval}',
            {table}.startDate) AS interval,
            AVG({value}) AS average, SUM({value}) AS sum,
            MIN({value}) AS min, MAX({value}) AS max, COUNT(*) AS count,
            unit FROM {table} {join_clause}
            WHERE {type_filter(table, record_type)}
            {"AND sourceName = $source_name" if source_name else ""}
            {f"AND {table}.startDate >= $date_from" if date_from else ""}
            {f"AND {table}.startDate <= $date_to" if date_to else ""}
            GROUP BY interval, {table}.type, sourceName, unit ORDER BY interval ASC
        """,
                params=query_params,
            ),
        )
    return client.format_response(results)


@ttl_cache(**_default_cache)
def get_sleep_summary_from_duckdb(
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    result = _get_con().sql(f"""
        SELECT DATE_TRUNC('day', startDate) AS night, textValue AS stage,
        COUNT(*) AS segment_count,
        SUM(date_diff('minute', startDate, endDate)) AS total_minutes
        FROM records WHERE type = 'HKCategoryTypeIdentifierSleepAnalysis'
        {f"AND startDate >= '{date_from}'" if date_from else ""}
        {f"AND startDate <= '{date_to}'" if date_to else ""}
        GROUP BY night, stage ORDER BY night DESC, stage
    """)
    return client.format_response(result)


@ttl_cache(
    maxsize=64,
    ttl_seconds=settings.DUCKDB_QUERY_CACHE_TTL_SECONDS,
    enabled=_cache_enabled,
)
def search_values_from_duckdb(
    record_type: RecordType | WorkoutType | str | None,
    value: str,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    table = get_table(record_type)
    join_clause = join_string(table)

    result = _get_con().sql(f"""
        SELECT * FROM {table} {join_clause} WHERE textValue = '{value}'
        {f"AND {table}.type = '{record_type}'" if record_type else ""}
        {f"AND startDate >= '{date_from}'" if date_from else ""}
        {f"AND startDate <= '{date_to}'" if date_to else ""}
        ORDER BY startDate DESC
    """)
    return client.format_response(result)


logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO, filename="duckdb.log", format="%(message)s")
    logger.info("Starting logging for duckdb queries")

    logger.info("-----------------")
    logger.info(f"records for get_health_summary_from_duckdb: {get_health_summary_from_duckdb()}")
    logger.info("-----------------")
    logger.info(
        f"records for get_statistics_by_type_duckdb:"
        f" {get_statistics_by_type_from_duckdb('HKWorkoutActivityTypeRunning')}",
    )
    logger.info("-----------------")
    logger.info(
        f"records for get_trend_data_duckdb: {
            get_trend_data_from_duckdb(
                'HKWorkoutActivityTypeRunning',
                date_from='2016-01-01T00:00:00+00:00',
                date_to='2016-12-31T23:59:59+00:00',
            )
        }",
    )
    logger.info("-----------------")
    pars = HealthRecordSearchParams(
        limit=20,
        record_type="HKWorkoutActivityTypeRunning",
        date_from="2016-01-01T00:00:00+00:00",
        date_to="2016-12-31T23:59:59+00:00",
    )
    logger.info(
        f"records for search_health_records_from_duckdb: {search_health_records_from_duckdb(pars)}",
    )
    logger.info("-----------------")
    logger.info("Finished logging")


if __name__ == "__main__":
    main()
