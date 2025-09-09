from typing import Any, Hashable

import duckdb

from app.schemas.record import RecordType, IntervalType, HealthRecordSearchParams
from app.services.duck import DuckDBClient
from app.services.health.sql_helpers import (
    build_value_range,
    fill_query
)

client = DuckDBClient()



def fill_query(params: HealthRecordSearchParams) -> str:
    conditions = []

    query = f"SELECT * FROM read_parquet('{client.path}') WHERE 1=1"
    if params.record_type:
        conditions.append(f" type = '{params.record_type}'")
    if params.source_name:
        conditions.append(f" source_name = '{params.source_name}'")
    if params.date_from or params.date_to:
        conditions.append(build_value_range(params.date_from, params.date_to))
    if params.value_min or params.value_max:
        conditions.append(build_value_range(params.value_min, params.value_max))

    if conditions:
        query += " AND " + " AND ".join(conditions)
    query += f"LIMIT {params.limit}"
    return query


def get_health_summary_from_duckdb() -> dict[Hashable, Any]:
    response = duckdb.sql(
        f"SELECT type, COUNT(*) FROM read_parquet('{client.path}') GROUP BY type"
    )
    return client.format_response(response)


def search_health_records_from_duckdb(
    params: HealthRecordSearchParams,
) -> dict[Hashable, Any]:
    query: str = f"SELECT * FROM read_parquet('{client.path}') WHERE 1=1"
    query += fill_query(params)
    response = duckdb.sql(query)
    return client.format_response(response)


def get_statistics_by_type_from_duckdb(
    record_type: RecordType | str,
) -> dict[Hashable, Any]:
    result = duckdb.sql(f"""
                    SELECT type, COUNT(*), AVG(numerical),
                    SUM(numerical), MIN(numerical), MAX(numerical)
                    FROM read_parquet('{client.path}')
                    WHERE type = '{record_type}' GROUP BY type
                    """)
    return client.format_response(result)


def get_trend_data_from_duckdb(
    record_type: RecordType | str,
    interval: IntervalType = "month",
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[Hashable, Any]:
    result = duckdb.sql(f"""
        SELECT time_bucket(INTERVAL '1 {interval}', startDate) AS interval,
        AVG(numerical), MIN(numerical), MAX(numerical), COUNT(*) FROM read_parquet('{client.path}')
        WHERE type = '{record_type}' {f"AND startDate >= '{date_from}'" if date_from else ""} {f"AND startDate <= '{date_to}'" if date_to else ""}
        GROUP BY interval ORDER BY interval ASC 
    """)
    return client.format_response(result)
