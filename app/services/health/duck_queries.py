from typing import Any
from time import time

import duckdb

from app.schemas.record import RecordType, IntervalType, HealthRecordSearchParams
from app.services.duck import DuckDBClient
from app.services.health.sql_helpers import fill_query

client = DuckDBClient()


def get_health_summary_from_duckdb() -> list[dict[str, Any]]:
    response = duckdb.sql(
        f"SELECT type, COUNT(*) AS count FROM read_parquet('{client.path}') GROUP BY ALL"
    )
    return client.format_response(response)


def search_health_records_from_duckdb(
    params: HealthRecordSearchParams,
) -> list[dict[str, Any]]:
    query: str = f"SELECT * FROM read_parquet('{client.path}') WHERE 1=1"
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
        SELECT time_bucket(INTERVAL '1 {interval}', startDate) AS interval,
        AVG(value), MIN(value), MAX(value), COUNT(*) FROM read_parquet('{client.path}')
        WHERE type = '{record_type}' {f"AND startDate >= '{date_from}'" if date_from else ""} {f"AND startDate <= '{date_to}'" if date_to else ""}
        GROUP BY interval ORDER BY interval ASC
    """)
    return client.format_response(result)

if __name__ == "__main__":
    start = time()
    # print('records for get_health_summary_from_duckdb: ', get_health_summary_from_duckdb())
    print("time: ", time() - start)
    start = time()
    # print('records for get_statistics_by_type_duckdb: ', get_statistics_by_type_from_duckdb('HKQuantityTypeIdentifierHeartRate'))
    print("time: ", time() - start)
    start = time()
    # print('records for get_trend_data_duckdb: ', get_trend_data_from_duckdb('HKQuantityTypeIdentifierHeartRate', 'year', '2014-06-01', '2020-06-01'))
    print("time: ", time() - start)
    start = time()
    pars = HealthRecordSearchParams(
        record_type="HKQuantityTypeIdentifierBasalEnergyBurned", value_min="10", value_max="20"
    )
    print(
        "records for search_health_records_from_duckdb: ", (search_health_records_from_duckdb(pars))
    )
    print("time: ", time() - start)