from typing import Any

from fastmcp import FastMCP

from app.schemas.record import HealthRecordSearchParams, IntervalType, RecordType, WorkoutType
from app.services.health.duckdb_queries import (
    get_health_summary_from_duckdb,
    get_sleep_summary_from_duckdb,
    get_statistics_by_type_from_duckdb,
    get_trend_data_from_duckdb,
    search_health_records_from_duckdb,
    search_values_from_duckdb,
)

duckdb_reader_router = FastMCP(name="DuckDB Reader MCP")


@duckdb_reader_router.tool
def get_health_summary_duckdb() -> list[dict[str, Any]]:
    """
    Get a summary of Apple Health data from DuckDB.
    The function returns total record count, record type breakdown, and
     (optionally) a date range aggregation.

    Notes for LLM:
    - IMPORTANT - Do not guess, autofill, or assume any missing data.
    - Use this tool if you're not certain of the record type that
      should be called
    - If there are multiple databases available (DuckDB, Elasticsearch):
      first, ask the user which one he wants to use. DO NOT call any tools before
      the user specifies his intent.
    - If the user decides on an option, only use tools from this database,
      do not switch over to another until the user specifies that he wants
      to use a different one. You do not have to keep asking whether
      the user wants to use the same database that he used before.
    - If there is only one database available (DuckDB, Elasticsearch):
      you can use the tools from this database without the user specifying it.
    """
    try:
        return get_health_summary_from_duckdb()
    except Exception as e:
        return [{"error": f"Failed to get health summary: {str(e)}"}]


@duckdb_reader_router.tool
def search_health_records_duckdb(
    record_type: RecordType | WorkoutType | list[str] | str | None = None,
    source_name: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    min_workout_duration: str | None = None,
    max_workout_duration: str | None = None,
    value_min: str | None = None,
    value_max: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Search health records in DuckDB with flexible query building.

    Parameters:
    - record_type: The type of health record to search for (see namespace notes below).
    - source_name: Filter by the device/app that recorded the data (e.g. "Rob’s iPhone").
    - date_from, date_to: Optional ISO8601 date strings for filtering date range.
    - min_workout_duration, max_workout_duration: Optional duration bounds for workouts.
    - value_min, value_max: Optional numeric value bounds for quantity samples.
    - limit: Maximum number of records to return (default 10).

    Notes for LLMs:
    - record_type accepts two distinct namespaces, and they are NOT interchangeable:
      * "HKQuantityTypeIdentifier*" (e.g. "HKQuantityTypeIdentifierDistanceWalkingRunning")
        — individual samples, queried from the records table.
      * "HKWorkoutActivityType*" (e.g. "HKWorkoutActivityTypeWalking",
        "HKWorkoutActivityTypeRunning", "HKWorkoutActivityTypeCycling") — whole
        workout/exercise SESSIONS with a start/end time and duration, queried from
        the workouts table. Use this namespace to check whether a workout was
        logged, not the quantity-sample one — a lack of quantity samples does not
        mean no workout exists.
      If unsure which type strings are actually present in the data, call
      get_health_summary_duckdb first — it lists every type (both namespaces)
      with a record count.
    - record_type also accepts a LIST of type strings to pull several metrics in one
      call instead of one call per metric (e.g. record_type=["HKQuantityTypeIdentifierDietaryProtein",
      "HKQuantityTypeIdentifierDietaryCarbohydrates", "HKQuantityTypeIdentifierDietaryFatTotal"]).
      `limit` then applies PER type, not to the combined total — so limit=10 with 3 types
      returns up to 10 rows of each, up to 30 total, not 10 total. All types in the list
      must be from the SAME namespace (all "HKQuantityTypeIdentifier*"/"HKCategoryTypeIdentifier*"
      or all "HKWorkoutActivityType*") — mixing namespaces raises an error, since they live in
      different tables and can't be queried together in one call.
    - This function should return a list of health record documents (dicts)
      matching the search criteria ordered by date from most to least recent.
    - Each document in the list should represent a single health record as stored in ClickHouse.
    - If an error occurs, the function should return a list with a single dict
      containing an ‘error’ key and the error message.
    - Use this to retrieve structured health data for further analysis, filtering, or display.
    - Example source_name: "Rob’s iPhone", "Polar Flow", "Sync Solver".
    - Example date_from/date_to: "2020-01-01T00:00:00+00:00"
    - Example value_min/value_max: "10", "100.5"
    - IMPORTANT - Do not guess, autofill, or assume any missing data.
    - This tool can be used to search for most recent records of a given type,
      in which case you should use this tool with a limit of 1.
    - If there are multiple databases available (DuckDB, Elasticsearch):
      first, ask the user which one he wants to use. DO NOT call any tools before
      the user specifies his intent.
    - If the user decides on an option, only use tools from this database,
      do not switch over to another until the user specifies that he wants
      to use a different one. You do not have to keep asking whether
      the user wants to use the same database that he used before.
    - If there is only one database available (DuckDB, Elasticsearch):
      you can use the tools from this database without the user specifying it.
    """
    try:
        params = HealthRecordSearchParams(
            record_type=record_type,
            source_name=source_name,
            date_from=date_from,
            date_to=date_to,
            min_workout_duration=min_workout_duration,
            max_workout_duration=max_workout_duration,
            value_min=value_min,
            value_max=value_max,
            limit=limit,
        )
        return search_health_records_from_duckdb(params)
    except Exception as e:
        return [{"error": f"Failed to search health records: {str(e)}"}]


@duckdb_reader_router.tool
def get_statistics_by_type_duckdb(
    record_type: RecordType | WorkoutType | list[str] | str,
    source_name: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    """
    Get comprehensive statistics for a specific health record type from DuckDB.

    Parameters:
    - record_type: The type of health record to analyze. Use RecordType for
      most frequent types. Use str if that type is beyond RecordType scope.
      Also accepts a LIST of type strings to get statistics for several metrics
      in one call instead of one call per metric — the result has one row per
      type. All types in the list must be from the same namespace/table (all
      quantity/category types, or all workout types); mixing raises an error.
    - source_name: Optional — restrict to one device/app (e.g. "Rob’s Apple Watch"),
      instead of returning all sources and filtering client-side.
    - date_from, date_to: Optional ISO8601 date strings for filtering date range.
      Without these, statistics are computed over ALL TIME — pass both to scope
      the aggregate to a specific period (e.g. a report's current period).

    Returns:
    - record_type: The analyzed record type
    - total_count: Total number of records of this type in the index
    - value_statistics: Statistical summary of the 'value' field including:
      * count: Number of records with values
      * min: Minimum value recorded
      * max: Maximum value recorded
      * avg: Average value across all records
      * sum: Sum of all values
    - sources: Breakdown of records by source device/app (e.g., "Rob's iPhone", "Polar Flow")

    Notes for LLMs:
    - This function provides comprehensive statistical analysis for any health record type.
    - The value_statistics object contains all basic statistics (count, min,
      max, avg, sum) for the 'value' field.
    - The sources breakdown shows which devices/apps contributed data for this record type.
    - Example types: "HKQuantityTypeIdentifierStepCount",
      "HKQuantityTypeIdentifierBodyMassIndex", "HKQuantityTypeIdentifierHeartRate", etc.
    - record_type also accepts "HKWorkoutActivityType*" values (e.g.
      "HKWorkoutActivityTypeWalking", "HKWorkoutActivityTypeCycling") to get
      statistics for whole workout sessions rather than individual quantity
      samples — these are a separate namespace/table from "HKQuantityTypeIdentifier*"
      types, not an alternative name for the same data. If unsure which type
      strings exist in the data, call get_health_summary_duckdb first.
    - Use this function to understand the distribution, range, and trends of
     specific health metrics.
    - The function is useful for health analysis, identifying outliers, and
      understanding data quality.
    - This tool can also be used to figure out the value of the record with
      the shortest/longest duration or highest/lowest value
    - IMPORTANT - Do not guess, autofill, or assume any missing data.
    - If there are multiple databases available (DuckDB, Elasticsearch):
      first, ask the user which one he wants to use. DO NOT call any tools before
      the user specifies his intent.
    - If the user decides on an option, only use tools from this database,
      do not switch over to another until the user specifies that he wants
      to use a different one. You do not have to keep asking whether
      the user wants to use the same database that he used before.
    - If there is only one database available (DuckDB, Elasticsearch):
      you can use the tools from this database without the user specifying it.
    """
    try:
        return get_statistics_by_type_from_duckdb(record_type, source_name, date_from, date_to)
    except Exception as e:
        return [{"error": f"Failed to get statistics: {str(e)}"}]


@duckdb_reader_router.tool
def get_trend_data_duckdb(
    record_type: RecordType | WorkoutType | list[str] | str,
    interval: IntervalType = "month",
    date_from: str | None = None,
    date_to: str | None = None,
    source_name: str | None = None,
) -> list[dict[str, Any]]:
    """
    Get trend data for a specific health record type over time using DuckDB
     date histogram aggregation.

    Parameters:
    - record_type: The type of health record to analyze (e.g., "HKQuantityTypeIdentifierStepCount").
      Also accepts a LIST of type strings to get trends for several metrics in one
      call instead of one call per metric — results are tagged by type, one set of
      buckets per type. All types in the list must be from the same namespace/table
      (all quantity/category types, or all workout types); mixing raises an error.
    - interval: Time interval for aggregation.
    - date_from, date_to: Optional ISO8601 date strings for filtering date range
    - source_name: Optional — restrict to one device/app (e.g. "Rob’s Apple Watch"),
      instead of returning all sources and filtering client-side.

    Returns:
    - record_type: The analyzed record type
    - device: The device on which the data was recorded
    - interval: The time interval used
    - trend_data: List of time buckets with statistics for each period:
      * date: The time period (ISO string)
      * value_sum: Sum of values for the period
      * avg_value: Average value for the period
      * min_value: Minimum value for the period
      * max_value: Maximum value for the period
      * count: Number of records in the period

    Notes for LLMs:
    - record_type also accepts "HKWorkoutActivityType*" values (e.g.
      "HKWorkoutActivityTypeWalking", "HKWorkoutActivityTypeCycling") to get
      trends over whole workout sessions rather than individual quantity samples
      — a separate namespace/table from "HKQuantityTypeIdentifier*" types, not
      an alternative name for the same data. If unsure which type strings exist
      in the data, call get_health_summary_duckdb first.
    - Use this to analyze trends, patterns, and seasonal variations in health data
    - Keep in mind that when there is data from multiple devices spanning the same
      time period, there is a possibility of data being duplicated. Inform the user
      of this possibility if you see multiple devices in the same time period.
    - If a user asks you to sum up some values from their health records, DO NOT
      search for records and write a script to sum them, instead, use this tool:
      if they ask to sum data from a year, use this tool with date_from set as the
      beginning of the year and date_to as the end of the year, with an interval
      of 'year'
    - The function automatically handles date filtering if date_from/date_to are provided
    - IMPORTANT - interval must be one of: "day", "week", "month", or "year".
      Do not use other values.
    - Do not guess, autofill, or assume any missing data.
    - If there are multiple databases available (DuckDB, Elasticsearch):
      first, ask the user which one he wants to use. DO NOT call any tools before
      the user specifies his intent.
    - If the user decides on an option, only use tools from this database,
      do not switch over to another until the user specifies that he wants
      to use a different one. You do not have to keep asking whether
      the user wants to use the same database that he used before.
    - If there is only one database available (DuckDB, Elasticsearch):
      you can use the tools from this database without the user specifying it.
    """
    try:
        return get_trend_data_from_duckdb(record_type, interval, date_from, date_to, source_name)
    except Exception as e:
        return [{"error": f"Failed to get trend data: {str(e)}"}]


@duckdb_reader_router.tool
def get_sleep_summary_duckdb(
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    """
    Get sleep stage durations (Deep/Core/REM/Awake/InBed) per night from DuckDB.

    Parameters:
    - date_from, date_to: Optional ISO8601 date strings for filtering date range.

    Returns a list of rows, one per (night, stage), each with:
    - night: The calendar day the sleep segment started on
    - stage: The sleep stage category, e.g. "HKCategoryValueSleepAnalysisAsleepDeep",
      "HKCategoryValueSleepAnalysisAsleepREM", "HKCategoryValueSleepAnalysisAsleepCore",
      "HKCategoryValueSleepAnalysisAwake", "HKCategoryValueSleepAnalysisInBed"
    - segment_count: Number of logged segments for that stage that night
    - total_minutes: Total minutes spent in that stage that night

    Notes for LLMs:
    - Use this instead of get_statistics_by_type_duckdb/get_trend_data_duckdb for sleep
      analysis: "HKCategoryTypeIdentifierSleepAnalysis" records store a categorical stage
      label, not a numeric value, so avg/sum from those tools are always 0 for sleep.
      This tool derives duration from each segment's startDate/endDate instead.
    - "night" groups by the calendar day the segment started on, so a sleep session that
      starts late one evening and ends the next morning is grouped under the start day.
    - Do not guess, autofill, or assume any missing data.
    - If there are multiple databases available (DuckDB, Elasticsearch):
      first, ask the user which one he wants to use. DO NOT call any tools before
      the user specifies his intent.
    - If the user decides on an option, only use tools from this database,
      do not switch over to another until the user specifies that he wants
      to use a different one. You do not have to keep asking whether
      the user wants to use the same database that he used before.
    - If there is only one database available (DuckDB, Elasticsearch):
      you can use the tools from this database without the user specifying it.
    """
    try:
        return get_sleep_summary_from_duckdb(date_from, date_to)
    except Exception as e:
        return [{"error": f"Failed to get sleep summary: {str(e)}"}]


@duckdb_reader_router.tool
def search_values_duckdb(
    record_type: RecordType | WorkoutType | str | None,
    value: str,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    """
    Search for records with exactly matching values (including text) using DuckDB.

    Parameters:
    - record_type: The type of health record to analyze (e.g., "HKQuantityTypeIdentifierStepCount")
    - value: Value to search for in the data
    - date_from, date_to: Optional ISO8601 date strings for filtering date range

    Notes for LLMs:
    - record_type also accepts "HKWorkoutActivityType*" values (e.g.
      "HKWorkoutActivityTypeWalking") to search within workout sessions rather
      than individual quantity samples — a separate namespace/table from
      "HKQuantityTypeIdentifier*" types. If unsure which type strings exist in
      the data, call get_health_summary_duckdb first.
    - Use this to search for specific values (for example statistical outliers) in health data
    - It can also be used for text values: e.g.
      you can search for "HKCategoryTypeIdentifierSleepAnalysis"
      records with the value of "HKCategoryValueSleepAnalysisAsleepDeep"
    - The function automatically handles date filtering if date_from/date_to are provided
    - Do not guess, autofill, or assume any missing data.
    - If there are multiple databases available (DuckDB, Elasticsearch):
      first, ask the user which one he wants to use. DO NOT call any tools before
      the user specifies his intent.
    - If the user decides on an option, only use tools from this database,
      do not switch over to another until the user specifies that he wants
      to use a different one. You do not have to keep asking whether
      the user wants to use the same database that he used before.
    - If there is only one database available (DuckDB, Elasticsearch):
      you can use the tools from this database without the user specifying it.
    """
    try:
        return search_values_from_duckdb(record_type, value, date_from, date_to)
    except Exception as e:
        return [{"error": f"Failed to search for values: {str(e)}"}]
