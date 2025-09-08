from typing import Any

from app.services.ch import CHClient
from app.schemas.record import RecordType, IntervalType, HealthRecordSearchParams


ch = CHClient()


def build_value_range(valuemin: str | None, valuemax: str | None) -> str | None:
    if valuemax and valuemin:
        return f"value >= '{valuemin}' and value <= '{valuemax}'"
    if valuemin:
        return f"value >= '{valuemin}'"
    if valuemax:
        return f"value <= '{valuemax}'"
    return None


def fill_query(params: HealthRecordSearchParams) -> str:
    conditions = []

    query = f"SELECT * FROM {ch.db_name}.{ch.table_name} WHERE 1=1"
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


def get_health_summary_from_ch() -> dict[str, Any]:
    return ch.inquire(f"SELECT type, COUNT(*) FROM {ch.db_name}.{ch.table_name} GROUP BY type")


def search_health_records_from_ch(params: HealthRecordSearchParams) -> dict[str, Any]:
    query: str = fill_query(params)
    return ch.inquire(query)


def get_statistics_by_type_from_ch(record_type: RecordType | str) -> dict[str, Any]:
    return ch.inquire(
        f"SELECT type, COUNT(*), AVG(numerical), SUM(numerical), MIN(numerical), MAX(numerical) FROM {ch.db_name}.{ch.table_name} WHERE type = '{record_type}' GROUP BY type"
    )


def get_trend_data_from_ch(
    record_type: RecordType | str,
    interval: IntervalType = "month",
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    return ch.inquire(f"""
        SELECT toStartOfInterval(startDate, INTERVAL 1 {interval}) AS interval,
        AVG(numerical), MIN(numerical), MAX(numerical), COUNT(*) FROM {ch.db_name}.{ch.table_name}
        WHERE type = '{record_type}' {f"AND startDate >= '{date_from}'" if date_from else ""} {f"AND startDate <= '{date_to}'" if date_to else ""}
        GROUP BY interval ORDER BY interval ASC
    """)
