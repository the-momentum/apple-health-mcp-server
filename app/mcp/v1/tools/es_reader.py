from typing import Any
from fastmcp import FastMCP

from app.schemas.record import RecordType, IntervalType, HealthRecordSearchParams
from app.services.health.elasticsearch import (
    get_health_summary_from_es,
    search_health_records_logic,
    get_statistics_by_type_logic,
    get_trend_data_logic,
)

es_reader_router = FastMCP(name="ES Reader MCP")


@es_reader_router.tool
def get_health_summary_es() -> dict[str, Any]:
    """
    Get a summary of Apple Health data from Elasticsearch.
    The function returns total record count, record type breakdown, and (optionally) a date range aggregation.
    """
    try:
        return get_health_summary_from_es()
    except Exception as e:
        return {"error": f"Failed to get health summary from ES: {str(e)}"}


@es_reader_router.tool
def search_health_records_es(params: HealthRecordSearchParams) -> list[dict[str, Any]]:
    """
    Search health records in Elasticsearch with flexible query building.

    Parameters:
    - params: HealthRecordSearchParams object containing all search/filter parameters.

    Notes for LLMs:
    - This function should return a list of health record documents (dicts) matching the search criteria.
    - Each document in the list should represent a single health record as stored in Elasticsearch.
    - If an error occurs, the function should return a list with a single dict containing an 'error' key and the error message.
    - Use this to retrieve structured health data for further analysis, filtering, or display.
    - Example source_name: "Rob’s iPhone", "Polar Flow", "Sync Solver".
    - Example date_from/date_to: "2020-01-01T00:00:00+00:00"
    - Example value_min/value_max: "10", "100.5"
    - IMPORTANT - Do not guess, auto-fill, or assume any missing data.
    """
    try:
        return search_health_records_logic(params)
    except Exception as e:
        return [{"error": f"Failed to search health records: {str(e)}"}]


@es_reader_router.tool
def get_statistics_by_type_es(record_type: RecordType | str) -> dict[str, Any]:
    """
    Get comprehensive statistics for a specific health record type from Elasticsearch.

    Parameters:
    - record_type: The type of health record to analyze. Use RecordType for most frequent types. Use str if that type is beyond RecordType scope.

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
    - The value_statistics object contains all basic statistics (count, min, max, avg, sum) for the 'value' field.
    - The sources breakdown shows which devices/apps contributed data for this record type.
    - Example types: "HKQuantityTypeIdentifierStepCount", "HKQuantityTypeIdentifierBodyMassIndex", "HKQuantityTypeIdentifierHeartRate", etc.
    - Use this function to understand the distribution, range, and trends of specific health metrics.
    - The function is useful for health analysis, identifying outliers, and understanding data quality.
    - date_range key for query is commented, since it contained hardcoded from date, but you can use it anyway if you replace startDate with your data.
    - IMPORTANT - Do not guess, auto-fill, or assume any missing data.
    """
    try:
        return get_statistics_by_type_logic(record_type)
    except Exception as e:
        return {"error": f"Failed to get statistics: {str(e)}"}


@es_reader_router.tool
def get_trend_data_es(
    record_type: RecordType | str,
    interval: IntervalType = "month",
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    """
    Get trend data for a specific health record type over time using Elasticsearch date histogram aggregation.

    Parameters:
    - record_type: The type of health record to analyze (e.g., "HKQuantityTypeIdentifierStepCount")
    - interval: Time interval for aggregation.
    - date_from, date_to: Optional ISO8601 date strings for filtering date range

    Returns:
    - record_type: The analyzed record type
    - interval: The time interval used
    - trend_data: List of time buckets with statistics for each period:
      * date: The time period (ISO string)
      * avg_value: Average value for the period
      * min_value: Minimum value for the period
      * max_value: Maximum value for the period
      * count: Number of records in the period

    Notes for LLMs:
    - Use this to analyze trends, patterns, and seasonal variations in health data
    - The function automatically handles date filtering if date_from/date_to are provided
    - IMPORTANT - interval must be one of: "day", "week", "month", or "year". Do not use other values.
    - Do not guess, auto-fill, or assume any missing data.
    """
    try:
        return get_trend_data_logic(record_type, interval, date_from, date_to)
    except Exception as e:
        return {"error": f"Failed to get trend data: {str(e)}"}
