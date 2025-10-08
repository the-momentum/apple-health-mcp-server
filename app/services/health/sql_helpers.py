from typing import Any

from app.schemas.record import HealthRecordSearchParams

join_query: str = "INNER JOIN stats ON workouts.startDate = stats.startDate"


def join_string(table: str) -> str:
    if table == "workouts":
        return join_query
    return ""


def value_aggregates(table: str) -> list[str]:
    if table in ["workouts", "stats"]:
        return ["duration", "sum"]
    return ["value"]


def get_table(record_type: str | Any) -> str:
    if record_type.startswith("HKWorkout"):
        return "workouts"
    return "records"


def get_value_type(table: str | None) -> str:
    match table:
        case "records":
            return "value"
        case "workouts" | "stats":
            return "sum"
        case _:
            return "value"


def build_date(date_from: str | None, date_to: str | None, table: str) -> str | None:
    if date_from and date_to:
        return f"{table}.startDate >= '{date_from}' and {table}.startDate <= '{date_to}'"
    if date_from:
        return f"{table}.startDate >= '{date_from}'"
    if date_to:
        return f"{table}.startDate <= '{date_to}'"
    return None


def build_value_range(
    valuemin: str | None,
    valuemax: str | None,
    value_type: str | None,
) -> str | None:
    # value_type: str = get_value_type(table)

    if valuemax and valuemin:
        return f"{value_type} >= '{valuemin}' and {value_type} <= '{valuemax}'"
    if valuemin:
        return f"{value_type} >= '{valuemin}'"
    if valuemax:
        return f"{value_type} <= '{valuemax}'"
    return None


def fill_query(params: HealthRecordSearchParams) -> str:
    conditions: list[str] = []
    table = get_table(params.record_type)

    if table == "workouts":
        query: str = f" workouts {join_query} WHERE 1=1"
    else:
        query: str = " records WHERE 1=1"
    value_type = get_value_type(table)

    if params.record_type:
        conditions.append(f" {table}.type = '{params.record_type}'")
    if params.source_name:
        conditions.append(f" source_name = '{params.source_name}'")
    if params.date_from or params.date_to:
        conditions.append(build_date(params.date_from, params.date_to, table))
    if params.value_min or params.value_max:
        conditions.append(build_value_range(params.value_min, params.value_max, value_type))
    if params.min_workout_duration or params.max_workout_duration:
        conditions.append(build_value_range(params.value_min, params.value_max, "duration"))

    conditions = [condition for condition in conditions if condition is not None]

    if conditions:
        query += " AND " + " AND ".join(conditions)

    query += f"ORDER BY {table}.startDate DESC LIMIT {params.limit}"
    return query
