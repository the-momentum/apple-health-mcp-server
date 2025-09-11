from typing import Any

from app.config import settings
from app.schemas.record import HealthRecordSearchParams, IntervalType, RecordType
from app.services.es_client import ESClient

es_client = ESClient()


def _build_match_condition(field: str, value: Any) -> dict:
    return {"match": {field: value}}


def _build_range_condition(field: str, gte: Any = None, lte: Any = None) -> dict:
    cond = {}
    if gte is not None:
        cond["gte"] = gte
    if lte is not None:
        cond["lte"] = lte
    return {"range": {field: cond}} if cond else {}


def _run_es_query(query: dict) -> Any:
    return es_client.engine.search(index=settings.ES_INDEX, body=query)


def get_health_summary_from_es() -> dict[str, Any]:
    query = {
        "size": 0,
        "aggs": {
            "total_records": {"value_count": {"field": "type.keyword"}},
            "record_types": {"terms": {"field": "type.keyword", "size": 50}},
        },
    }
    response = _run_es_query(query)
    total_records_value = response["aggregations"]["total_records"]["value"]
    record_types = {
        bucket["key"]: bucket["doc_count"]
        for bucket in response["aggregations"]["record_types"]["buckets"]
    }
    return {
        "total_records": total_records_value,
        "record_types": record_types,
        "index_name": settings.ES_INDEX,
    }


def search_health_records_logic(params: HealthRecordSearchParams) -> list[dict[str, Any]]:
    must_conditions = []
    if params.record_type:
        must_conditions.append(_build_match_condition("type", params.record_type))
    if params.source_name:
        must_conditions.append(_build_match_condition("sourceName", params.source_name))
    if params.date_from or params.date_to:
        range_cond = _build_range_condition("dateComponents", params.date_from, params.date_to)
        if range_cond:
            must_conditions.append(range_cond)
    if params.value_min is not None or params.value_max is not None:
        range_cond = _build_range_condition("value", params.value_min, params.value_max)
        if range_cond:
            must_conditions.append(range_cond)
    query: dict[str, Any]
    if must_conditions:
        query = {"query": {"bool": {"must": must_conditions}}}
    else:
        query = {"query": {"match_all": {}}}
    query["size"] = params.limit
    response = _run_es_query(query)
    return [hit["_source"] for hit in response["hits"]["hits"]]


def get_statistics_by_type_logic(record_type: RecordType | str) -> dict[str, Any]:
    query = {
        "size": 0,
        "query": _build_match_condition("type", record_type),
        "aggs": {
            "value_stats": {"stats": {"field": "value"}},
        },
    }
    response = _run_es_query(query)
    return {
        "record_type": record_type,
        "total_count": response["hits"]["total"]["value"],
        "value_statistics": response["aggregations"]["value_stats"],
    }


def get_trend_data_logic(
    record_type: RecordType | str,
    interval: IntervalType = "month",
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    must_conditions = [{"match": {"type": record_type}}]
    if date_from or date_to:
        range_cond = _build_range_condition("dateComponents", date_from, date_to)
        if range_cond:
            must_conditions.append(range_cond)
    query = {
        "size": 0,
        "query": {"bool": {"must": must_conditions}},
        "aggs": {
            "trend_over_time": {
                "date_histogram": {"field": "dateComponents", "calendar_interval": interval},
                "aggs": {
                    "avg_value": {"avg": {"field": "value"}},
                    "min_value": {"min": {"field": "value"}},
                    "max_value": {"max": {"field": "value"}},
                    "count": {"value_count": {"field": "value"}},
                },
            },
        },
    }
    response = _run_es_query(query)
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
            },
        )
    return {"record_type": record_type, "interval": interval, "trend_data": trend_data}


def search_values_logic(
    record_type: RecordType | str | None,
    value: str,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    must_conditions = [{"match": {"textvalue": value}}]
    if record_type:
        must_conditions.append({"match": {"type": record_type}})
    if date_from or date_to:
        range_cond = _build_range_condition("dateComponents", date_from, date_to)
        if range_cond:
            must_conditions.append(range_cond)
    query = {"query": {"bool": {"must": must_conditions}}}
    response = _run_es_query(query)
    return [hit["_source"] for hit in response["hits"]["hits"]]