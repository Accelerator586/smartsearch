# Smart Search CLI Contract

## Entrypoints

- `smart-search` is the primary CLI.
- `smart-search` should resolve from the user's PATH.
- This bundled skill is maintained with the `smartsearch` repository.
- Private API keys should be saved with `smart-search setup` or `smart-search config set`.
- Environment variables remain supported for CI and advanced users, and override the local config file.
- Do not depend on MCP inline `env` values or committed API-key environment variables for CLI use.

## Commands

- `smart-search search QUERY [--platform NAME] [--model ID] [--extra-sources N] [--timeout SECONDS] [--format json|markdown] [--output PATH]`
- `smart-search fetch URL [--format json|markdown] [--output PATH]`
- `smart-search exa-search QUERY [--num-results N] [--search-type neural|keyword|auto] [--include-text] [--include-highlights] [--start-published-date YYYY-MM-DD] [--include-domains CSV] [--exclude-domains CSV] [--category NAME] [--format json|markdown] [--output PATH]`
- `smart-search exa-similar URL [--num-results N] [--format json|markdown] [--output PATH]`
- `smart-search map URL [--instructions TEXT] [--max-depth N] [--max-breadth N] [--limit N] [--timeout SECONDS] [--format json|markdown] [--output PATH]`
- `smart-search doctor [--format json|markdown] [--output PATH]`
- `smart-search setup [--non-interactive] [--api-url URL] [--api-key KEY] [--api-mode auto|xai-responses|chat-completions] [--xai-tools CSV] [--model ID] [--exa-key KEY] [--tavily-key KEY] [--firecrawl-key KEY] [--format json|markdown] [--output PATH]`
- `smart-search config path [--format json|markdown] [--output PATH]`
- `smart-search config list [--format json|markdown] [--output PATH]`
- `smart-search config set KEY VALUE [--format json|markdown] [--output PATH]`
- `smart-search config unset KEY [--format json|markdown] [--output PATH]`
- `smart-search model set MODEL [--format json] [--output PATH]`
- `smart-search model current [--format json] [--output PATH]`
- `smart-search regression`

## JSON Expectations

Successful search output includes `ok`, `query`, `primary_api_mode`, `content`, `sources`, `sources_count`, and `elapsed_ms`. Each source should include at least `url` when available.

Fetch output includes `ok`, `url`, `provider`, `content`, and `elapsed_ms`.

Exa search output includes `ok`, `query`, `search_type`, `results`, `total`, and `elapsed_ms` when successful.

Exa similar output includes `ok`, `url`, `results`, `total`, and `elapsed_ms` when successful.

Map output includes `ok`, `base_url`, `results`, `response_time`, `url`, and `elapsed_ms` when successful.

Diagnostic output masks keys, reports `config_file` / `config_sources` / `primary_api_mode` / `primary_api_mode_source`, and includes connection test objects for the primary endpoint, Exa, Tavily, and Firecrawl. Firecrawl currently reports whether `FIRECRAWL_API_KEY` is configured; it is not a live Firecrawl request.

Setup and config output should include `ok` and `config_file`. Saved API keys must be masked in command output.

Search timeout output uses `ok=false`, `error_type=network_error`, includes the timeout seconds in `error`, keeps `query`, `content`, `sources`, and `sources_count`, and exits with code `4`.

## Provider Routing

- `search` calls the resolved primary endpoint. `SMART_SEARCH_API_MODE=auto` maps `https://api.x.ai/v1` to official xAI Responses API `/responses`; all other URLs map to OpenAI-compatible Chat Completions `/chat/completions`.
- `SMART_SEARCH_API_MODE` may be explicitly set to `xai-responses` or `chat-completions`.
- `SMART_SEARCH_XAI_TOOLS` applies only to xAI Responses mode and supports only `web_search` and `x_search`.
- Chat Completions mode must not send xAI `web_search` / `x_search` tools or legacy `search_parameters`; xAI Chat Completions Live Search is deprecated.
- `search` calls Tavily and/or Firecrawl only when `--extra-sources` is greater than 0.
- If both Tavily and Firecrawl are configured, `search --extra-sources N` gives about 60% of extra source slots to Tavily and the remainder to Firecrawl.
- `fetch` tries Tavily first, then Firecrawl as fallback when Tavily returns no content.
- `map` uses Tavily only.
- `exa-search` and `exa-similar` use Exa only.
- Runtime config priority is environment variables first, then local config file, then defaults.
- `setup` and `config` read/write the local Smart Search config file and do not call providers.
- `model current` and `model set` read/write the local Smart Search config file and do not call providers.

## Routing Heuristics

- Use `exa-search --include-domains` when official documentation domains are known.
- Use `exa-search --start-published-date` for recency-constrained source discovery.
- Use `exa-similar` when a known good page is available and adjacent sources are needed.
- Use `fetch --format markdown` for user-supplied URLs or when exact page text matters.
- Use `map` before fetching many pages from a documentation site.
- Keep `search --extra-sources` small (`1` to `3`) unless broad coverage is requested.

## Exit Codes

- `0`: success
- `2`: parameter error
- `3`: configuration error
- `4`: network or upstream error
- `5`: runtime or parse error

## Regression

Run `smart-search regression` before considering CLI or skill changes complete. It should run offline pytest coverage for CLI, service, and skill contract behavior.

## Tool Policy

Web research through this skill should use `smart-search` CLI. If the CLI is unavailable, report the blocker and recovery steps instead of silently falling back to another web-search route.
