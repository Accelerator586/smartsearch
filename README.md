# smart-search

CLI-first web research for coding agents. It combines:

- OpenAI-compatible chat completions for broad web-enabled search answers.
- Exa for low-noise source discovery.
- Tavily and Firecrawl for URL extraction, site maps, and extra source coverage.

This repository is intentionally CLI-only and exposes only the `smart-search` command.

## Install

```powershell
uv venv
uv pip install -e ".[dev]"
```

## Configure

Set the primary OpenAI-compatible endpoint:

```powershell
$env:SMART_SEARCH_API_URL = "https://example.com/v1"
$env:SMART_SEARCH_API_KEY = "..."
$env:SMART_SEARCH_MODEL = "grok-4-fast"
```

Optional providers:

```powershell
$env:EXA_API_KEY = "..."
$env:TAVILY_API_KEY = "..."
$env:FIRECRAWL_API_KEY = "..."
```

Supported primary settings:

- `SMART_SEARCH_API_URL`
- `SMART_SEARCH_API_KEY`
- `SMART_SEARCH_MODEL`
- `SMART_SEARCH_DEBUG`
- `SMART_SEARCH_LOG_LEVEL`
- `SMART_SEARCH_LOG_DIR`
- `SMART_SEARCH_RETRY_MAX_ATTEMPTS`
- `SMART_SEARCH_RETRY_MULTIPLIER`
- `SMART_SEARCH_RETRY_MAX_WAIT`
- `SMART_SEARCH_OUTPUT_CLEANUP`
- `SMART_SEARCH_LOG_TO_FILE`
- `SSL_VERIFY`

Provider settings:

- `EXA_API_KEY`
- `EXA_BASE_URL`
- `EXA_TIMEOUT_SECONDS`
- `TAVILY_API_KEY`
- `TAVILY_API_URL`
- `TAVILY_ENABLED`
- `FIRECRAWL_API_KEY`
- `FIRECRAWL_API_URL`

## Commands

```powershell
smart-search doctor --format json
smart-search search "OpenAI Responses API documentation" --extra-sources 3 --timeout 90 --format json
smart-search exa-search "OpenAI Responses API documentation" --num-results 5 --include-highlights --format json
smart-search fetch "https://example.com" --format markdown
smart-search map "https://docs.example.com" --max-depth 1 --limit 50 --format json
smart-search model current
smart-search regression
```

`doctor` masks configured secrets in its output. Do not put secret values in
README files, shell history examples, issue reports, or test fixtures.
