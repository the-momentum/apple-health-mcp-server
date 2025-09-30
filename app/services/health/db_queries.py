from typing import Any

import duckdb
from fastmcp.server.dependencies import get_context

from app.schemas.record import HealthRecordSearchParams, IntervalType, RecordType
from app.services.duckdb_client import DuckDBClient
from app.services.health.sql_helpers import fill_query, get_table, get_value_type

client = DuckDBClient()
con = duckdb.connect(client.path, read_only=True)


def get_health_summary_from_duckdb() -> list[dict[str, Any]]:
    try:
        records = con.sql(
            """SELECT type, COUNT(*) AS count FROM records
            GROUP BY type ORDER BY count DESC""",
        )
        workouts = con.sql(
            """SELECT workouts.type, COUNT(*) AS count FROM workouts
            INNER JOIN stats ON workouts.startDate = stats.startDate
            GROUP BY workouts.type ORDER BY count DESC""",
        )
    except duckdb.IOException:
        try:
            ctx = get_context()
            ctx.error("Failed to connect to DuckDB")
        except RuntimeError:
            print("Failed to connect to DuckDB")
        return [{"status_code": 400, "error": "failed to connect to DuckDB", "path": client.path}]

    return client.format_response([records, workouts])


def search_health_records_from_duckdb(
    params: HealthRecordSearchParams,
) -> list[dict[str, Any]]:
    query: str = "SELECT * FROM"
    query += fill_query(params)
    response = con.sql(query)
    return client.format_response(response)


def get_statistics_by_type_from_duckdb(
    record_type: RecordType | str,
) -> list[dict[str, Any]]:
    table = get_table(record_type)
    value = get_value_type(record_type)
    result = con.sql(f"""
                    SELECT type, COUNT(*) AS count, AVG({value}) AS average,
                    SUM({value}) AS sum, MIN({value}) AS min, MAX({value}) AS max
                    FROM {table}
                    WHERE {table}.type = '{record_type}' GROUP BY type
                    """)
    return client.format_response(result)


def get_trend_data_from_duckdb(
    record_type: RecordType | str,
    interval: IntervalType = "month",
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    table = get_table(record_type)
    value = get_value_type(table)
    result = con.sql(f"""
        SELECT sourceName, time_bucket(INTERVAL '1 {interval}', startDate) AS interval,
        AVG({value}) AS average, SUM({value}) AS sum,
        MIN({value}) AS min, MAX({value}) AS max, COUNT(*) AS count
        FROM records
        WHERE type = '{record_type}'
        {f"AND startDate >= '{date_from}'" if date_from else ""}
        {f"AND startDate <= '{date_to}'" if date_to else ""}
        GROUP BY interval, sourceName ORDER BY interval ASC
    """)
    return client.format_response(result)


def search_values_from_duckdb(
    record_type: RecordType | str | None,
    value: str,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    table = get_table(record_type)
    result = con.sql(f"""
        SELECT * FROM {table} WHERE textValue = '{value}'
        {f"AND {table}.type = '{record_type}'" if record_type else ""}
        {f"AND startDate >= '{date_from}'" if date_from else ""}
        {f"AND startDate <= '{date_to}'" if date_to else ""}
    """)
    return client.format_response(result)


if __name__ == "__main__":
    from time import time

    # print(len(client.format_response(con.sql("""
    #         SELECT * FROM records WHERE value=0;
    # """))))
    start = time()
    # con.sql("SHOW TABLES").show()
    print("records for get_health_summary_from_duckdb: ", len(get_health_summary_from_duckdb()))
    # print("time: ", time() - start)
    start = time()
    print(
        "records for get_statistics_by_type_duckdb: ",
        len(get_statistics_by_type_from_duckdb("HKQuantityTypeIdentifierHeartRate")),
    )
    # print("time: ", time() - start)
    start = time()
    print(
        "records for get_trend_data_duckdb: ",
        len(
            get_trend_data_from_duckdb(
                "HKQuantityTypeIdentifierHeartRate",
            ),
        ),
    )
    # print("time: ", time() - start)
    start = time()
    pars = HealthRecordSearchParams(
        record_type="HKWorkoutActivityTypeRunning",
        value_min="30",
        value_max="45",
    )
    # con.sql("SHOW TABLES").show()
    # con.sql("SELECT * FROM workouts").show()
    print(
        "records for search_health_records_from_duckdb: ",
        len(search_health_records_from_duckdb(pars)),
    )
    # print("time: ", time() - start)
