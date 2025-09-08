from app.schemas.record import RecordType, IntervalType, HealthRecordSearchParams


def build_value_range(valuemin: str | None, valuemax: str | None) -> str | None:
    if valuemax and valuemin:
        return f"value >= '{valuemin}' and value <= '{valuemax}'"
    if valuemin:
        return f"value >= '{valuemin}'"
    if valuemax:
        return f"value <= '{valuemax}'"
    return None

def fill_query(params: HealthRecordSearchParams) -> str:
    conditions: list[str] = []
    query: str = ""

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