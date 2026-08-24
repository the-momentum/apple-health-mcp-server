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


def get_table(record_type: str | list[str] | Any) -> str:
    types = record_type if isinstance(record_type, list) else [record_type]
    is_workout = [bool(t) and t.startswith("HKWorkout") for t in types]
    if any(is_workout) and not all(is_workout):
        raise ValueError(
            "record_type mixes HKWorkoutActivityType* with other types — these live in "
            "separate tables (workouts vs records) and can't be queried together. "
            "Split into separate calls per table.",
        )
    return "workouts" if any(is_workout) else "records"


def type_filter(table: str, record_type: str | list[str]) -> str:
    if isinstance(record_type, list):
        quoted = ", ".join(f"'{t}'" for t in record_type)
        return f"{table}.type IN ({quoted})"
    return f"{table}.type = '{record_type}'"


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
        conditions.append(f" {type_filter(table, params.record_type)}")
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

    if isinstance(params.record_type, list):
        query += (
            f" QUALIFY ROW_NUMBER() OVER ("
            f"PARTITION BY {table}.type ORDER BY {table}.startDate DESC"
            f") <= {params.limit} ORDER BY {table}.startDate DESC"
        )
    else:
        query += f"ORDER BY {table}.startDate DESC LIMIT {params.limit}"
    return query
