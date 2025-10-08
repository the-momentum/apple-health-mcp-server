import logging
from typing import Any

import duckdb

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
    records = con.sql(
        """SELECT type, COUNT(*) AS count FROM records
        GROUP BY type ORDER BY count DESC""",
    )
    workouts = con.sql(
        f"""SELECT workouts.type, COUNT(*) AS count FROM workouts {join_query}
        GROUP BY workouts.type ORDER BY count DESC""",
    )

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
    complimentary_table = "stats" if table == "workouts" else "records"
    join_clause = join_string(table)
    values = value_aggregates(table)
    results = []
    value = values[0]
    for value in values:
        results.append(
            con.sql(f"""
                    SELECT {table}.type, {complimentary_table}.type AS stat_type, COUNT(*) AS count,
                    AVG({value}) AS average, SUM({value}) AS sum, MIN({value}) AS min,
                    MAX({value}) AS max, unit FROM {table} {join_clause}
                    WHERE {table}.type = '{record_type}' GROUP BY {table}.type,
                    {complimentary_table}.type, unit
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
        min_workout_duration="45",
        max_workout_duration="53"
    )
    logger.info(
        f"records for search_health_records_from_duckdb: {search_health_records_from_duckdb(pars)}",
    )
    logger.info("-----------------")
    logger.info("Finished logging")


if __name__ == "__main__":
    main()
