from typing import Any

import duckdb
from fastmcp.server.dependencies import get_context

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
    value_aggregates,
)

client = DuckDBClient()
con = duckdb.connect(client.path, read_only=True)


def get_health_summary_from_duckdb() -> list[dict[str, Any]]:
    try:
        records = con.sql(
            """SELECT type, COUNT(*) AS count FROM records
            GROUP BY type ORDER BY count DESC""",
        )
        workouts = con.sql(
            f"""SELECT workouts.type, COUNT(*) AS count FROM workouts {join_query}
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
    record_type: RecordType | WorkoutType | str,
) -> list[dict[str, Any]]:
    table = get_table(record_type)
    join_clause = join_string(table)
    values = value_aggregates(table)
    results = []

    for value in values:
        results.append(
            con.sql(f"""
                    SELECT {table}.type, COUNT(*) AS count, AVG({value}) AS average,
                    SUM({value}) AS sum, MIN({value}) AS min, MAX({value}) AS max,
                    unit FROM {table} {join_clause}
                    WHERE {table}.type = '{record_type}' GROUP BY {table}.type, unit
                    """),
        )
    return client.format_response(results)


def get_trend_data_from_duckdb(
    record_type: RecordType | WorkoutType | str,
    interval: IntervalType = "month",
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    table = get_table(record_type)
    join_clause = join_string(table)
    values = value_aggregates(table)
    results = []

    for value in values:
        results.append(
            con.sql(f"""
            SELECT {table}.type, sourceName, time_bucket(INTERVAL '1 {interval}',
            {table}.startDate) AS interval,
            AVG({value}) AS average, SUM({value}) AS sum,
            MIN({value}) AS min, MAX({value}) AS max, COUNT(*) AS count,
            unit FROM {table} {join_clause}
            WHERE {table}.type = '{record_type}'
            {f"AND {table}.startDate >= '{date_from}'" if date_from else ""}
            {f"AND {table}.startDate <= '{date_to}'" if date_to else ""}
            GROUP BY interval, {table}.type, sourceName, unit ORDER BY interval ASC
        """),
        )
    return client.format_response(results)


def search_values_from_duckdb(
    record_type: RecordType | WorkoutType | str | None,
    value: str,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    table = get_table(record_type)
    join_clause = join_string(table)

    result = con.sql(f"""
        SELECT * FROM {table} {join_clause} WHERE textValue = '{value}'
        {f"AND {table}.type = '{record_type}'" if record_type else ""}
        {f"AND startDate >= '{date_from}'" if date_from else ""}
        {f"AND startDate <= '{date_to}'" if date_to else ""}
        ORDER BY startDate DESC
    """)
    return client.format_response(result)


if __name__ == "__main__":
    # from time import time

    # print(len(client.format_response(con.sql("""
    #         SELECT * FROM records WHERE value=0;
    # """))))
    # start = time()
    # con.sql("SHOW TABLES").show()
    print("records for get_health_summary_from_duckdb: ", len(get_health_summary_from_duckdb()))
    # print("time: ", time() - start)
    # start = time()
    print(
        "records for get_statistics_by_type_duckdb: ",
        len(get_statistics_by_type_from_duckdb("HKWorkoutActivityTypeRunning")),
    )
    # print("time: ", time() - start)
    # start = time()
    print(
        "records for get_trend_data_duckdb: ",
        (
            get_trend_data_from_duckdb(
                "HKWorkoutActivityTypeRunning",
            ),
        ),
    )
    # print("time: ", time() - start)
    # start = time()
    pars = HealthRecordSearchParams(
        limit=20,
        record_type="HKWorkoutActivityTypeRunning",
        max_workout_duration="60",
        min_workout_duration="30",
    )
    # con.sql("SHOW TABLES").show()
    # con.sql("SELECT * FROM workouts").show()
    print(
        "records for search_health_records_from_duckdb: ",
        len(search_health_records_from_duckdb(pars)),
    )
    # print("time: ", time() - start)
