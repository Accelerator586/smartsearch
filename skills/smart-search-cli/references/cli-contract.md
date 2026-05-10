# Smart Search CLI Contract

## Entrypoints

- `smart-search` is the primary CLI.
- `smart-search` should resolve from the user's PATH.
- This bundled skill is maintained with the `smartsearch` repository.
- Private API keys should be loaded by the user's shell, profile, or local wrapper outside the repository.
- Do not depend on MCP inline `env` values or committed API-key environment variables for CLI use.

## Commands

- `smart-search search QUERY [--platform NAME] [--model ID] [--extra-sources N] [--timeout SECONDS] [--format json|markdown] [--output PATH]`
- `smart-search fetch URL [--format json|markdown] [--output PATH]`
- `smart-search exa-search QUERY [--num-results N] [--search-type neural|keyword|auto] [--include-text] [--include-highlights] [--start-published-date YYYY-MM-DD] [--include-domains CSV] [--exclude-domains CSV] [--category NAME] [--format json|markdown] [--output PATH]`
- `smart-search exa-similar URL [--num-results N] [--format json|markdown] [--output PATH]`
- `smart-search map URL [--instructions TEXT] [--max-depth N] [--max-breadth N] [--limit N] [--timeout SECONDS] [--format json|markdown] [--output PATH]`
- `smart-search doctor [--format json|markdown] [--output PATH]`
- `smart-search model set MODEL [--format json] [--output PATH]`
- `smart-search model current [--format json] [--output PATH]`
- `smart-search regression`

## JSON Expectations

Successful search output includes `ok`, `query`, `content`, `sources`, `sources_count`, and `elapsed_ms`. Each source should include at least `url` when available.

Fetch output includes `ok`, `url`, `provider`, `content`, and `elapsed_ms`.

Exa search output includes `ok`, `query`, `search_type`, `results`, `total`, and `elapsed_ms` when successful.

Exa similar output includes `ok`, `url`, `results`, `total`, and `elapsed_ms` when successful.

Map output includes `ok`, `base_url`, `results`, `response_time`, `url`, and `elapsed_ms` when successful.

Diagnostic output masks keys and includes connection test objects for the primary OpenAI-compatible endpoint, Exa, Tavily, and Firecrawl. Firecrawl currently reports whether `FIRECRAWL_API_KEY` is configured; it is not a live Firecrawl request.

Search timeout output uses `ok=false`, `error_type=network_error`, includes the timeout seconds in `error`, keeps `query`, `content`, `sources`, and `sources_count`, and exits with code `4`.

## Provider Routing

- `search` always calls the primary OpenAI-compatible endpoint. It calls Tavily and/or Firecrawl only when `--extra-sources` is greater than 0.
- If both Tavily and Firecrawl are configured, `search --extra-sources N` gives about 60% of extra source slots to Tavily and the remainder to Firecrawl.
- `fetch` tries Tavily first, then Firecrawl as fallback when Tavily returns no content.
- `map` uses Tavily only.
- `exa-search` and `exa-similar` use Exa only.
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
