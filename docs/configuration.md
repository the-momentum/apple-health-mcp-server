# Configuration

[← Back to README](../README.md)

Settings come from `config/.env` (copy `config/.env.example`). All are optional; relative paths
resolve from the repo root. Unknown keys in `config/.env` are ignored.

| Variable | Description | Default |
|----------|-------------|---------|
| `RAW_XML_PATH` | Apple Health `export.xml` read by `make duckdb` | `raw.xml` |
| `DUCKDB_FILENAME` | Imported health database (local path or `http(s)://` URL) | `data/applehealth.duckdb` |
| `LOGS_DUCKDB_FILENAME` | Writable fueling-log database | `data/manual_logs.duckdb` |
| `REPORTS_DUCKDB_FILENAME` | Writable report-history database | `data/health_reports.duckdb` |
| `IMPORT_LOOKBACK_MONTHS` | Only import records from the last N months. The whole XML is parsed regardless, so a limit saves DB size and peak import memory (about 0.4 GB per 1M records), not time; leave unset unless memory is tight. Fewer `IMPORT_WORKERS` does not reduce memory | unset (everything) |
| `IMPORT_WORKERS` | Parallel import processes | CPU count |
| `CHUNK_SIZE` | Records written per batch during import | `50000` |
| `DUCKDB_QUERY_CACHE_ENABLED` | In-process cache for DuckDB reads | `true` |
| `DUCKDB_QUERY_CACHE_TTL_SECONDS` | Cache entry lifetime | `1800` |
| `DUCKDB_QUERY_CACHE_MAXSIZE` | Max cached entries per query type | `256` |
