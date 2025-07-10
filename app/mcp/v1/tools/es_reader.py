from typing import Any
from fastmcp import FastMCP

from app.config import settings
from app.services.es import ESClient
from app.schemas.record import RecordType


es_reader_router = FastMCP(name="ES Reader MCP")
es_client = ESClient()


@es_reader_router.tool
def get_health_summary_from_es() -> dict[str, Any]:
    """
    Get a summary of Apple Health data from Elasticsearch.
    - type: one of ["HKQuantityTypeIdentifierStepCount", "HKQuantityTypeIdentifierBodyMassIndex", "HKQuantityTypeIdentifierHeartRate", ...] -> check RecordType literal, but it contains most frequent types only
    - startDate: ISO8601 date string (optional, used for date range aggregations)
    - value: float
    The function returns total record count, record type breakdown, and (optionally) a date range aggregation.
    """
    try:
        query = {
            "size": 0,
            "aggs": {
                "total_records": {"value_count": {"field": "type.keyword"}},
                "record_types": {"terms": {"field": "type.keyword", "size": 50}},
                # Date range aggregation is optional; can be added by LLM or user if needed
                # "date_range": {
                #     "date_range": {
                #         "field": "dateComponent",
                #         "ranges": [
                #             {"from": "2010-01-01", "to": "now"}
                #         ]
                #     }
                # }
            },
        }

        response = es_client.engine.search(index=settings.ES_INDEX, body=query)

        total_records = response["aggregations"]["total_records"]["value"]
        record_types = {
            bucket["key"]: bucket["doc_count"]
            for bucket in response["aggregations"]["record_types"]["buckets"]
        }

        return {
            "total_records": total_records,
            "record_types": record_types,
            "index_name": settings.ES_INDEX,
        }

    except Exception as e:
        return {"error": f"Failed to get health summary from ES: {str(e)}"}


@es_reader_router.tool
def search_health_records(
    record_type: RecordType | str | None = None,
    source_name: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    value_min: str | None = None,
    value_max: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Search health records in Elasticsearch with flexible query building.

    Parameters:
    - record_type: The type of health record to search for. Use RecordType for most frequent types (e.g., "HKQuantityTypeIdentifierStepCount", "HKQuantityTypeIdentifierBodyMassIndex", etc.), or provide a custom string for rare or custom types. Set to None to match all types.
    - source_name: (Optional) The device or app that generated the record (e.g., "Rob’s iPhone", "Polar Flow").
    - date_from, date_to: (Optional) ISO8601 date strings to filter by date range (applies to the 'dateComponents' field).
    - value_min, value_max: (Optional) Minimum/maximum value for the 'value' field (float, but can be passed as string for flexibility).
    - limit: Maximum number of records to return.

    Notes for LLMs:
    - RecordType contains only the most frequent types, but you can use any string for custom/rare types.
    - If you want to match all types, set record_type to None.
    - The function returns a list of health record documents matching the criteria.
    - Example types: "HKQuantityTypeIdentifierStepCount", "HKQuantityTypeIdentifierBodyMassIndex", "HKQuantityTypeIdentifierHeartRate", "HKQuantityTypeIdentifierBodyMass", "HKQuantityTypeIdentifierHeight", "HKQuantityTypeIdentifierDietaryWater", etc.
    - Example source_name: "Rob’s iPhone", "Polar Flow", "Sync Solver".
    - Example date_from/date_to: "2020-01-01T00:00:00+00:00"
    - Example value_min/value_max: "10", "100.5"
    """
    try:
        must_conditions = []

        if record_type:
            must_conditions.append({"match": {"type": record_type}})

        if source_name:
            must_conditions.append({"match": {"sourceName": source_name}})

        if date_from or date_to:
            date_range = {}
            if date_from:
                date_range["gte"] = date_from
            if date_to:
                date_range["lte"] = date_to
            must_conditions.append({"range": {"dateComponents": date_range}})

        if value_min is not None or value_max is not None:
            value_range = {}
            if value_min is not None:
                value_range["gte"] = value_min
            if value_max is not None:
                value_range["lte"] = value_max
            must_conditions.append({"range": {"value": value_range}})

        # Build the final query
        query: dict[str, Any]
        if must_conditions:
            query = {"query": {"bool": {"must": must_conditions}}}
        else:
            query = {"query": {"match_all": {}}}

        query["size"] = limit

        response = es_client.engine.search(index=settings.ES_INDEX, body=query)

        return [hit["_source"] for hit in response["hits"]["hits"]]

    except Exception as e:
        return [{"error": f"Failed to search health records: {str(e)}"}]


# @es_reader_router.tool
# def get_records_by_type(record_type: RecordType, limit: int = 20) -> list[dict[str, Any]]:
#     """Get all records of a specific type from Elasticsearch."""
#     try:
#         query = {
#             "query": {"match": {"type": record_type}},
#             "size": limit,
#             "sort": [{"dateComponents": {"order": "desc"}}]
#         }

#         response = es_client.engine.search(index=settings.ES_INDEX, body=query)

#         return [hit["_source"] for hit in response["hits"]["hits"]]

#     except Exception as e:
#         return [{"error": f"Failed to get records by type: {str(e)}"}]


@es_reader_router.tool
def get_statistics_by_type(record_type: RecordType | str) -> dict[str, Any]:
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
    """
    try:
        query = {
            "size": 0,
            "query": {"match": {"type": record_type}},
            "aggs": {
                "value_stats": {"stats": {"field": "value"}},
                # "date_range": {
                #     "date_range": {
                #         "field": "dateComponents",
                #         "ranges": [
                #             {"from": "2010-01-01", "to": "now"}
                #         ]
                #     }
                # },
                # "sources": {"terms": {"field": "sourceName.keyword", "size": 10}}
            },
        }

        response = es_client.engine.search(index=settings.ES_INDEX, body=query)

        return {
            "record_type": record_type,
            "total_count": response["hits"]["total"]["value"],
            "value_statistics": response["aggregations"]["value_stats"],
            # "sources": {bucket["key"]: bucket["doc_count"] for bucket in response["aggregations"]["sources"]["buckets"]}
        }

    except Exception as e:
        return {"error": f"Failed to get statistics: {str(e)}"}


@es_reader_router.tool
def get_trend_data(
    record_type: RecordType | str,
    interval: str = "month",
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    """
    Get trend data for a specific health record type over time using Elasticsearch date histogram aggregation.

    Parameters:
    - record_type: The type of health record to analyze (e.g., "HKQuantityTypeIdentifierStepCount")
    - interval: Time interval for aggregation ("day", "week", "month", "year")
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
    - Common intervals: "day" for daily patterns, "month" for monthly trends, "year" for annual analysis
    - The function automatically handles date filtering if date_from/date_to are provided
    """
    try:
        date_filter = {}
        if date_from:
            date_filter["gte"] = date_from
        if date_to:
            date_filter["lte"] = date_to

        query = {
            "size": 0,
            "query": {"bool": {"must": [{"match": {"type": record_type}}]}},
            "aggs": {
                "trend_over_time": {
                    "date_histogram": {"field": "dateComponents", "calendar_interval": interval},
                    "aggs": {
                        "avg_value": {"avg": {"field": "value"}},
                        "min_value": {"min": {"field": "value"}},
                        "max_value": {"max": {"field": "value"}},
                        "count": {"value_count": {"field": "value"}},
                    },
                }
            },
        }

        if date_filter:
            query["query"]["bool"]["must"].append({"range": {"dateComponents": date_filter}})

        response = es_client.engine.search(index=settings.ES_INDEX, body=query)

        buckets = response["aggregations"]["trend_over_time"]["buckets"]
        trend_data = []

        for bucket in buckets:
            trend_data.append(
                {
                    "date": bucket["key_as_string"],
                    "avg_value": bucket["avg_value"]["value"],
                    "min_value": bucket["min_value"]["value"],
                    "max_value": bucket["max_value"]["value"],
                    "count": bucket["count"]["value"],
                }
            )

        return {"record_type": record_type, "interval": interval, "trend_data": trend_data}

    except Exception as e:
        return {"error": f"Failed to get trend data: {str(e)}"}


# @es_reader_router.tool
# def search_by_text(query: str, limit: int = 20) -> list[dict[str, Any]]:
#     """
#     Search health data by text query across multiple fields using Elasticsearch multi_match.

#     Parameters:
#     - query: Text string to search for (e.g., "iPhone", "heart", "steps")
#     - limit: Maximum number of records to return (default: 20)

#     Returns:
#     - List of health record documents matching the text query, sorted by date (newest first)
#     - Each document contains all fields: type, value, dateComponents, sourceName, unit, etc.

#     Notes for LLMs:
#     - Searches across type, sourceName, unit, and value fields simultaneously
#     - Use for finding records by device name, health metric type, or partial text matches
#     - Results are automatically sorted by date (most recent first)
#     - Example queries: "iPhone", "Polar", "steps", "heart", "weight"
#     """
#     try:
#         search_query = {
#             "query": {
#                 "multi_match": {
#                     "query": query,
#                     "fields": ["type", "sourceName", "unit", "value"],
#                     "type": "best_fields"
#                 }
#             },
#             "size": limit,
#             "sort": [{"dateComponents": {"order": "desc"}}]
#         }

#         response = es_client.engine.search(index=settings.ES_INDEX, body=search_query)

#         return [hit["_source"] for hit in response["hits"]["hits"]]

#     except Exception as e:
#         return [{"error": f"Failed to search by text: {str(e)}"}]
