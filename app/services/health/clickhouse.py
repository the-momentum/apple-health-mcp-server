from typing import Any

from app.schemas.record import HealthRecordSearchParams, IntervalType, RecordType
from app.services.ch_client import CHClient
from app.services.health.sql_helpers import fill_query

ch = CHClient()


def get_health_summary_from_ch() -> dict[str, Any]:
    return ch.inquire(f"SELECT type, COUNT(*) FROM {ch.db_name}.{ch.table_name} GROUP BY type")


def search_health_records_from_ch(params: HealthRecordSearchParams) -> dict[str, Any]:
    query: str = f"SELECT * FROM {ch.db_name}.{ch.table_name}"
    query += fill_query(params)
    return ch.inquire(query)


def get_statistics_by_type_from_ch(record_type: RecordType | str) -> dict[str, Any]:
    return ch.inquire(
        f"SELECT type, COUNT(*), AVG(value), SUM(value), MIN(value), "
        f"MAX(value) FROM {ch.db_name}.{ch.table_name} WHERE type = '{record_type}' "
        f"GROUP BY type",
    )


def get_trend_data_from_ch(
    record_type: RecordType | str,
    interval: IntervalType = "month",
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    return ch.inquire(f"""
        SELECT device, toStartOfInterval(startDate, INTERVAL 1 {interval}) AS interval,
        AVG(value) AS average, SUM(value) AS sum, MIN(value) AS min,
        MAX(value) AS max, COUNT(*) AS count FROM {ch.db_name}.{ch.table_name}
        WHERE type = '{record_type}'
        {f"AND startDate >= '{date_from}'" if date_from else ""}
        {f"AND startDate <= '{date_to}'" if date_to else ""}
        GROUP BY interval, device ORDER BY interval ASC
    """)


def search_values_from_ch(
    record_type: RecordType | str | None,
    value: str,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    return ch.inquire(f"""
        SELECT * FROM {ch.db_name}.{ch.table_name} WHERE textValue = '{value}'
        {f"AND type = '{record_type}'" if record_type else ""}
        {f"AND startDate >= '{date_from}'" if date_from else ""}
        {f"AND startDate <= '{date_to}'" if date_to else ""}
    """)
