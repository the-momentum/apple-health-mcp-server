from typing import Any

from app.services.ch_client import CHClient
from app.schemas.record import RecordType, IntervalType, HealthRecordSearchParams
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
