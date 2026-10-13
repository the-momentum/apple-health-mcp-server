<a name="readme-top"></a>

# Apple Health MCP Server

Connect your Apple Health export to any LLM client that supports MCP. You can ask about your data in plain language, with no SQL. It also logs ride and workout fueling next to your health data.

## 🚀 How-to

1. **Export from iPhone**: Health app → your profile picture → *Export All Health Data*. AirDrop or save `export.zip` to your Mac.
2. **Clone & install** (needs [uv](https://docs.astral.sh/uv/getting-started/installation/)):
   ```sh
   git clone https://github.com/ivisav/apple-health-mcp-server
   cd apple-health-mcp-server
   uv sync
   ```
3. **Put the export in the drop folder**. This creates `apple_health_export/export.xml`. Git ignores that folder's contents, so your health data is never committed.
   ```sh
   unzip ~/Downloads/export.zip -d .
   ```
4. **Configure**: copy the example env file and point it at the export:
   ```sh
   cp config/.env.example config/.env
   # in config/.env:
   RAW_XML_PATH="apple_health_export/export.xml"
   # optional: only import the last N months, e.g. 12 (default: everything; the
   # whole file is parsed either way, so a limit saves DB size and import memory,
   # not time)
   # IMPORT_LOOKBACK_MONTHS=12
   ```
5. **Import** into DuckDB (runs in parallel; safe to re-run):
   ```sh
   make duckdb
   ```
6. **Connect your MCP client** (e.g. Claude Desktop), then restart the client:
   ```json
   {
     "mcpServers": {
       "apple-health": {
         "command": "uv",
         "args": ["run", "--frozen", "--directory", "<repo-path>", "start"],
         "env": { "PATH": "<folder-containing-uv>" }
       }
     }
   }
   ```
7. **Updating later**: download a new export and repeat steps 3 and 5, then restart the MCP server. Each import rebuilds the database from scratch, so it never creates duplicates, and a failed run leaves the existing database untouched.

For a Docker setup, see **[Getting Started](docs/getting-started.md)**.

## 🛠️ Tools

| Tool | What it does |
|------|--------------|
| `get_health_summary_duckdb` | Record counts per data type |
| `search_health_records_duckdb` | Filtered record search (type(s), source, dates, values) |
| `get_statistics_by_type_duckdb` | count / min / max / avg / sum, filterable by source and dates |
| `get_trend_data_duckdb` | Day / week / month / year aggregations |
| `get_sleep_summary_duckdb` | Per-night Deep / Core / REM / Awake / In Bed minutes |
| `get_blood_pressure_summary_duckdb` | Systolic + diastolic (+ heart rate) joined into one reading per timestamp |
| `search_values_duckdb` | Exact value matches (including text) |
| `log_fueling_event` / `search_fueling_events` / `delete_fueling_event` | Manual log of drinks, gels, bars, etc. |
| `start_report_period` / `upsert_report_metrics` / `add_report_notes` / `get_report_history` / `get_report_trend` / `get_report_notes` | Weekly report history: per-period metrics and notes, week/month trends |

Full list: [MCP Tools](docs/mcp-tools.md).

## 📈 Report history

Weekly-report skills save each period's metrics, findings and flags with the `*_report_*` tools, and read back history or week/month trends in one small call instead of re-reading old reports or notes. The data lives in `data/health_reports.duckdb` (`REPORTS_DUCKDB_FILENAME`), which is created empty on first use, never touched by the importer, and kept out of git and the Docker image.

One-time import of an existing "Weekly Health Baselines" Apple Note (Markdown text or the Notes HTML body):
```sh
osascript -e 'tell application "Notes" to get body of (first note whose name starts with "Weekly Health Baselines")' > data/baselines.html
uv run scripts/import_baselines_note.py data/baselines.html --dry-run   # check periods + warnings
uv run scripts/import_baselines_note.py data/baselines.html             # safe to re-run
```

## ✨ What's new in this fork

- **Fueling log**: manual fueling events are stored in a separate writable DuckDB file (`LOGS_DUCKDB_FILENAME`). The importer never touches it, and every write is flushed to disk immediately.
- **Report history**: weekly-report skills store per-period metrics and findings in a separate writable DuckDB file (`REPORTS_DUCKDB_FILENAME`) and read back compact history and week/month trends instead of re-parsing notes.
- **Faster, safer import**: runs across multiple processes, rebuilds atomically (safe to repeat), optional `IMPORT_LOOKBACK_MONTHS` limits how far back it imports (full history is the default and recommended), and `make duckdb-reset` deletes the imported database.
- **Query cache**: an in-process TTL + LRU cache for DuckDB reads, configured with `DUCKDB_QUERY_CACHE_*` in `config/.env.example`.
- **Better filtering**: stats and trend tools accept a list of types plus source and date filters. Source names match even with Apple's curly apostrophes and non-breaking spaces (e.g. `Apple Watch`).
- **DuckDB only**: the upstream Elasticsearch, ClickHouse and XML direct-read backends are removed — one import pipeline, 16 tools, fewer dependencies.
- **Security**: tool arguments never reach SQL unchecked (bound as parameters, or validated as type names, ISO dates and numbers), and dependencies are kept free of applicable known vulnerabilities.
- **Correctness fixes**: food records nested inside a Correlation are no longer counted twice. Relative DuckDB paths now resolve from the repo root instead of the working directory.

## 🧑‍💻 Development

```sh
make test     # pytest with coverage
make check    # ruff lint + format check + ty
make format   # auto-fix

# dependency vulnerability audit
uv export --frozen --no-hashes --all-groups --no-emit-project > /tmp/req.txt && uvx pip-audit -r /tmp/req.txt --disable-pip --no-deps
```

After a re-import, restart the MCP server or wait out the cache TTL to see the new data.

## 📚 Docs

[Getting Started](docs/getting-started.md) · [Configuration](docs/configuration.md) · [MCP Tools](docs/mcp-tools.md) · [About & Architecture](docs/about.md)

## 🌱 Origins

This is a fork of **[the-momentum/apple-health-mcp-server](https://github.com/the-momentum/apple-health-mcp-server)**, built by [Momentum](https://themomentum.ai) ([demo video](https://github.com/user-attachments/assets/93ddbfb9-6da9-42c1-9872-815abce7e918)).

<div align="center">
  <img src="https://cdn.prod.website-files.com/66a1237564b8afdc9767dd3d/66df7b326efdddf8c1af9dbb_Momentum%20Logo.svg" height="60">

  [![Contact us](https://img.shields.io/badge/Contact%20us-AFF476.svg?style=for-the-badge&logo=mail&logoColor=black)](mailto:hello@themomentum.ai?subject=Apple%20Health%20MCP%20Server%20Inquiry)
  [![Visit Momentum](https://img.shields.io/badge/Visit%20Momentum-1f6ff9.svg?style=for-the-badge&logo=safari&logoColor=white)](https://themomentum.ai)
  [![MIT License](https://img.shields.io/badge/License-MIT-636f5a.svg?style=for-the-badge&logo=opensourceinitiative&logoColor=white)](LICENSE)
</div>

> [!NOTE]
> **This project has evolved into [Open Wearables](https://github.com/the-momentum/open-wearables)** - self-hosted platform to unify wearable health data from multiple devices, including Apple Health. Open Wearables also provides an MCP server and a companion app for continuous Apple Health data sync, eliminating the need for manual XML exports. Check it out: [github.com/the-momentum/open-wearables](https://github.com/the-momentum/open-wearables)

### 💼 About Momentum
This project is part of Momentum’s open-source ecosystem, where we make healthcare technology more secure, interoperable, and AI-ready. Our goal is to help HealthTech teams adopt standards such as FHIR safely and efficiently. We are healthcare AI development experts, recognized by FT1000, Deloitte Fast 50, and Forbes for building scalable, HIPAA-compliant solutions that power next-generation healthcare innovation.

📖 Want to learn from our experience? Read our insights → <a href="https://www.themomentum.ai/blog">themomentum.ai/blog</a>. 
Interested? <a href="http://themomentum.ai/lets-talk">Let's talk</a>!

<div align="center">
  <p><em>Built with ❤️ by <a href="https://themomentum.ai">Momentum</a> • Transforming healthcare data management with AI</em></p>
</div>

<p align="right">(<a href="#readme-top">back to top</a>)</p>
