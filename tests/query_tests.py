import pytest

from app.services.health.duckdb_queries import (
    get_health_summary_from_duckdb,
    search_health_records_from_duckdb,
    get_statistics_by_type_from_duckdb,
    get_trend_data_from_duckdb,
    search_values_from_duckdb
)

