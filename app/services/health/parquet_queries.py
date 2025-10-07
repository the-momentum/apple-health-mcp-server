from typing import Any

import duckdb

from app.schemas.record import HealthRecordSearchParams, IntervalType, RecordType
from app.services.duckdb_client import DuckDBClient
from app.services.health.sql_helpers import fill_query

client = DuckDBClient()


def get_health_summary_from_duckdb() -> list[dict[str, Any]]:
    response = duckdb.sql(
        f"""SELECT type, COUNT(*) AS count FROM read_parquet('{client.path}')
         GROUP BY type ORDER BY count DESC""",
    )
    return client.format_response(response)


def search_health_records_from_duckdb(
    params: HealthRecordSearchParams,
) -> list[dict[str, Any]]:
    query: str = f"SELECT * FROM read_parquet('{client.path}')"
    query += fill_query(params)
    response = duckdb.sql(query)
    return client.format_response(response)


def get_statistics_by_type_from_duckdb(
    record_type: RecordType | str,
) -> list[dict[str, Any]]:
    result = duckdb.sql(f"""
                    SELECT type, COUNT(*) AS count, AVG(value) AS average,
                    SUM(value) AS sum, MIN(value) AS min, MAX(value) AS max
                    FROM read_parquet('{client.path}')
                    WHERE type = '{record_type}' GROUP BY type
                    """)
    return client.format_response(result)


def get_trend_data_from_duckdb(
    record_type: RecordType | str,
    interval: IntervalType = "month",
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    result = duckdb.sql(f"""
        SELECT device, time_bucket(INTERVAL '1 {interval}', startDate) AS interval,
        AVG(value) AS average, SUM(value) AS sum,
        MIN(value) AS min, MAX(value) AS max, COUNT(*) AS count
        FROM read_parquet('{client.path}')
        WHERE type = '{record_type}'
        {f"AND startDate >= '{date_from}'" if date_from else ""}
        {f"AND startDate <= '{date_to}'" if date_to else ""}
        GROUP BY interval, device ORDER BY interval ASC
    """)
    return client.format_response(result)


def search_values_from_duckdb(
    record_type: RecordType | str | None,
    value: str,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    result = duckdb.sql(f"""
        SELECT * FROM read_parquet('{client.path}') WHERE textvalue = '{value}'
        {f"AND type = '{record_type}'" if record_type else ""}
        {f"AND startDate >= '{date_from}'" if date_from else ""}
        {f"AND startDate <= '{date_to}'" if date_to else ""}
    """)
    return client.format_response(result)
