from app.schemas.record import HealthRecordSearchParams

def build_date(date_from: str | None, date_to: str | None) -> str | None:
    if date_from and date_to:
        return f"startDate >= '{date_from}' and startDate <= '{date_to}'"
    if date_from:
        return f"startDate >= '{date_from}'"
    if date_to:
        return f"startDate <= '{date_to}'"
    return None

def build_value_range(valuemin: str | None, valuemax: str | None) -> str | None:
    if valuemax and valuemin:
        return f"numerical >= '{valuemin}' and numerical <= '{valuemax}'"
    if valuemin:
        return f"numerical >= '{valuemin}'"
    if valuemax:
        return f"numerical <= '{valuemax}'"
    return None

def fill_query(params: HealthRecordSearchParams) -> str:
    conditions: list[str] = []
    query: str = ""

    if params.record_type:
        conditions.append(f" type = '{params.record_type}'")
    if params.source_name:
        conditions.append(f" source_name = '{params.source_name}'")
    if params.date_from or params.date_to:
        conditions.append(build_date(params.date_from, params.date_to))
    if params.value_min or params.value_max:
        conditions.append(build_value_range(params.value_min, params.value_max))

    if conditions:
        query += " AND " + " AND ".join(conditions)
    query += f"LIMIT {params.limit}"
    return query