from time import time
from typing import Any

from app.services.ch import CHIndexer
from app.schemas.record import RecordType, IntervalType, HealthRecordSearchParams


def build_value_range(valuemin, valuemax) -> str | None:
    if valuemax and valuemin:
        return f"value >= '{valuemin}' and value <= '{valuemax}'"
    if valuemin:
        return f"value >= '{valuemin}'"
    if valuemax:
        return f"value >= '{valuemax}'"
    return None


def fill_query(params: HealthRecordSearchParams) -> str:
    ch = CHIndexer()
    conditions = []

    query = f"SELECT * FROM {ch.dbname}.{ch.name} WHERE 1=1"
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
    query += f'LIMIT {params.limit}'
    return query


def get_health_summary_from_ch() -> dict[str, Any]:
    ch = CHIndexer()
    return ch.inquire(f"SELECT type, COUNT(*) FROM {ch.dbname}.{ch.name} GROUP BY type")


def search_health_records_from_ch(params: HealthRecordSearchParams) -> dict[str, Any]:
    query: str = fill_query(params)
    ch = CHIndexer()
    return ch.inquire(query)


def get_statistics_by_type_from_ch(record_type: RecordType | str) -> dict[str, Any]:
    ch = CHIndexer()
    return ch.inquire(f"SELECT type, COUNT(*), AVG(numerical), SUM(numerical), MIN(numerical), MAX(numerical) FROM {ch.dbname}.{ch.name} WHERE type = '{record_type}' GROUP BY type")


def get_trend_data_from_ch(
    record_type: RecordType | str,
    interval: IntervalType = "month",
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    ch = CHIndexer()
    return ch.inquire(f"""
        SELECT toStartOfInterval(startDate, INTERVAL 1 {interval}) AS interval,
        AVG(numerical), MIN(numerical), MAX(numerical), COUNT(*) FROM {ch.dbname}.{ch.name}
        WHERE type = '{record_type}' {f"AND startDate >= '{date_from}'" if date_from else ''} {f"AND startDate <= '{date_to}'" if date_to else ''}
        GROUP BY interval ORDER BY interval ASC 
    """)


def update_db_ch() -> dict[str, str | bool]:
    ch = CHIndexer()
    try:
        ch.sess.sql(f"DROP TABLE IF EXISTS {ch.dbname}.{ch.name}")
        ch.run()
        return {"updated": True}
    except Exception as e:
        return {"updated": False,
                "error": str(e)}


if __name__ == '__main__':
    start = time()
    print('records for get_health_summary_from_ch: ', len(get_health_summary_from_ch()['data']))
    print('time: ', time() - start)
    start = time()
    print('records for get_statistics_by_type_ch: ', (get_statistics_by_type_from_ch('HKQuantityTypeIdentifierHeartRate')['data']))
    print('time: ', time() - start)
    start = time()
    print('records for get_trend_data_ch: ', (get_trend_data_from_ch('HKQuantityTypeIdentifierHeartRate', 'month', '2014-06-01', '2020-06-01')['data']))
    print('time: ', time() - start)
    start = time()
    pars = HealthRecordSearchParams(record_type='HKQuantityTypeIdentifierBasalEnergyBurned', value_min = '10', value_max = '20')
    print('records for search_health_records_from_ch: ', (search_health_records_from_ch(pars)['data']))
    print('time: ', time() - start)
