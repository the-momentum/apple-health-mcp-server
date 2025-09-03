from time import time

from app.services.ch import CHIndexer
from app.config import settings
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
    # if params.record_type:
    #     conditions.append(f" type = {params.record_type}")
    if params.source_name:
        conditions.append(f" source_name = {params.source_name}")
    if params.date_from or params.date_to:
        conditions.append(build_value_range(params.date_from, params.date_to))
    if params.value_min or params.value_max:
        conditions.append(build_value_range(params.value_min, params.value_max))

    if conditions:
        query += " AND " + " AND ".join(conditions)
    return query


def get_health_summary_from_ch() -> str:
    ch = CHIndexer()
    return ch.inquire(f"SELECT type, COUNT(*) FROM {ch.dbname}.{ch.name} GROUP BY type")


def search_health_records_from_ch(params: HealthRecordSearchParams) -> str:
    query: str = fill_query(params)
    ch = CHIndexer()
    # return query
    return ch.inquire(query)


def get_statistics_by_type_ch(record_type: RecordType | str):
    ch = CHIndexer()
    return ch.inquire(f"SELECT type, COUNT(*), AVG(numerical), SUM(numerical), MIN(numerical), MAX(numerical) FROM {ch.dbname}.{ch.name} WHERE 1 = 1 GROUP BY type")


def get_trend_data_ch(
    record_type: RecordType | str,
    interval: IntervalType = "month",
    date_from: str | None = None,
    date_to: str | None = None,
):
    ch = CHIndexer()
    return ch.inquire(f"""
        SELECT toStartOfInterval(startDate, INTERVAL 1 {interval}) AS interval,
        AVG(numerical), MIN(numerical), MAX(numerical), COUNT(*) FROM {ch.dbname}.{ch.name}
        WHERE 1=1 GROUP BY interval ORDER BY interval ASC 
    """)


class par():
    def __init__(self, pars):
        self.record_type = pars.get('record_type')
        self.source_name = pars.get('source_name')
        self.date_from = pars.get('date_from')
        self.date_to = pars.get('date_to')
        self.value_min = pars.get('value_min')
        self.value_max = pars.get('value_max')

if __name__ == '__main__':
    start = time()
    print('records for get_health_summary_from_ch: ', len(get_health_summary_from_ch()))
    print('time: ', time() - start)
    start = time()
    print('records for get_statistics_by_type_ch: ', len(get_statistics_by_type_ch('HKQuantityTypeIdentifierHeartRate')))
    print('time: ', time() - start)
    start = time()
    print('records for get_trend_data_ch: ', len(get_trend_data_ch('HKQuantityTypeIdentifierHeartRate', 'month', '2015-06-01', '2015-09-30')))
    print('time: ', time() - start)
    start = time()
    params = HealthRecordSearchParams(record_type='HKQuantityTypeIdentifierHeartRate', value_min = '10', value_max = '20')
    # params = par({"record_type": 'HKQuantityTypeIdentifierHeartRate', "value_min": '10', "value_max": '20'})
    print('records for search_health_records_from_ch: ', len(search_health_records_from_ch(params)))
    print('time: ', time() - start)
