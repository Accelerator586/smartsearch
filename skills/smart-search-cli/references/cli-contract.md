# Smart Search CLI Contract

## Entrypoints

- `smart-search` is the primary CLI.
- `smart-search --version`, `smart-search --v`, and `smart-search -v` print the installed version and exit with code `0`.
- `smart-search` should resolve from the user's PATH.
- This bundled skill is maintained with the `smartsearch` repository.
- Private API keys should be saved with `smart-search setup` or `smart-search config set`.
- Environment variables remain supported for CI and advanced users, and override the local config file.
- Do not depend on MCP inline `env` values or committed API-key environment variables for CLI use.
- On Windows with mise, the managed package name is `npm:@konbakuyomu/smart-search`; the executable remains `smart-search`. Diagnose mise managed installs with `mise ls "npm:@konbakuyomu/smart-search"` and `mise which smart-search` (the bare name `smart-search` is the bin, not a mise tool identifier).
- In sandboxed runtimes (Codex CLI, containers, CI) where subprocesses cannot read the user's `~/.config`, set `SMART_SEARCH_CONFIG_DIR` to an absolute writable path. The CLI uses it for both config and logs.

## Commands

- `smart-search search QUERY [--platform NAME] [--model ID] [--extra-sources N] [--validation fast|balanced|strict] [--fallback auto|off] [--providers auto|CSV] [--timeout SECONDS] [--format json|markdown|content] [--output PATH]`
- `smart-search fetch URL [--format json|markdown|content] [--output PATH]`
- `smart-search exa-search QUERY [--num-results N] [--search-type neural|keyword|auto] [--include-text] [--include-highlights] [--start-published-date YYYY-MM-DD] [--include-domains CSV] [--exclude-domains CSV] [--category NAME] [--format json|markdown|content] [--output PATH]`
- `smart-search exa-similar URL [--num-results N] [--format json|markdown|content] [--output PATH]`
- `smart-search zhipu-search QUERY [--count N] [--search-engine NAME] [--search-recency-filter VALUE] [--search-domain-filter DOMAIN] [--content-size medium|high] [--format json|markdown|content] [--output PATH]`
- `smart-search context7-library NAME [QUERY] [--format json|markdown|content] [--output PATH]`
- `smart-search context7-docs LIBRARY_ID QUERY [--format json|markdown|content] [--output PATH]`
- `smart-search map URL [--instructions TEXT] [--max-depth N] [--max-breadth N] [--limit N] [--timeout SECONDS] [--format json|markdown|content] [--output PATH]`
- `smart-search doctor [--format json|markdown|content] [--output PATH]`
- `smart-search setup [--lang zh|en] [--advanced] [--non-interactive] [--skip-skills] [--install-skills CSV] [--skills-root PATH] [--api-url URL] [--api-key KEY] [--api-mode auto|xai-responses|chat-completions] [--xai-tools CSV] [--model ID] [--xai-api-url URL] [--xai-api-key KEY] [--xai-model ID] [--xai-tools-explicit CSV] [--openai-compatible-api-url URL] [--openai-compatible-api-key KEY] [--openai-compatible-model ID] [--validation-level fast|balanced|strict] [--fallback-mode auto|off] [--minimum-profile standard|off] [--exa-key KEY] [--context7-key KEY] [--zhipu-key KEY] [--tavily-api-url URL] [--tavily-key KEY] [--firecrawl-api-url URL] [--firecrawl-key KEY] [--format json|markdown|content] [--output PATH]`
- `smart-search config path [--format json|markdown|content] [--output PATH]`
- `smart-search config list [--format json|markdown|content] [--output PATH]`
- `smart-search config set KEY VALUE [--format json|markdown|content] [--output PATH]`
- `smart-search config unset KEY [--format json|markdown|content] [--output PATH]`
- `smart-search model set MODEL [--format json|markdown|content] [--output PATH]`
- `smart-search model current [--format json|markdown|content] [--output PATH]`
- `smart-search regression`
- `smart-search smoke [--mode mock|live] [--mock] [--live] [--format json|markdown|content] [--output PATH]`
- `smart-search --version`

## Aliases

Top-level aliases must normalize to the same service behavior as their full command:

| Full command | Aliases |
| --- | --- |
| `smart-search --version` | `smart-search --v`, `smart-search -v` |
| `search` | `s` |
| `fetch` | `f` |
| `map` | `m` |
| `exa-search` | `exa`, `x` |
| `exa-similar` | `xs` |
| `zhipu-search` | `z`, `zp` |
| `context7-library` | `c7`, `ctx7` |
| `context7-docs` | `c7d`, `c7docs`, `ctx7-docs` |
| `doctor` | `d` |
| `setup` | `init` |
| `config` | `cfg` |
| `model` | `mdl` |
| `smoke` | `sm` |
| `regression` | `reg` |

Nested aliases:

| Full command | Aliases |
| --- | --- |
| `config path` | `cfg p` |
| `config list` | `cfg ls`, `cfg l` |
| `config set` | `cfg s` |
| `config unset` | `cfg rm`, `cfg u` |
| `model current` | `mdl cur`, `mdl c` |
| `model set` | `mdl s` |

## JSON Expectations

Successful search output includes `ok`, `query`, `primary_api_mode`, `content`, `sources`, `sources_count`, `primary_sources`, `primary_sources_count`, `extra_sources`, `extra_sources_count`, `source_warning`, `routing_decision`, `providers_used`, `provider_attempts`, `fallback_used`, `validation_level`, and `elapsed_ms`. Each source should include at least `url` when available.

`--format content` prints only the `content` field when present. JSON output remains parseable and uses readable non-ASCII text when the terminal encoding supports it.

Source provenance fields:

- `primary_sources`: sources explicitly extracted from the primary model/provider answer.
- `extra_sources`: parallel Tavily / Firecrawl candidates from `--extra-sources`; these are not automatic evidence for the generated `content`.
- `sources`: backward-compatible merged list from `primary_sources + extra_sources`, deduped by URL.
- `source_warning`: non-empty when extra source candidates were appended.

Fetch output includes `ok`, `url`, `provider`, `content`, and `elapsed_ms`.

Exa search output includes `ok`, `query`, `search_type`, `results`, `total`, and `elapsed_ms` when successful.

Exa similar output includes `ok`, `url`, `results`, `total`, and `elapsed_ms` when successful.

Zhipu search output includes `ok`, `query`, `provider`, `search_engine`, `results`, `total`, and `elapsed_ms` when successful.

Context7 library output includes `ok`, `query`, `provider`, `results`, `total`, and `elapsed_ms` when successful. Context7 docs output includes `ok`, `library_id`, `query`, `provider`, `results`, `total`, `content`, and `elapsed_ms` when successful.

Map output includes `ok`, `base_url`, `results`, `response_time`, `url`, and `elapsed_ms` when successful.

Diagnostic output masks keys, reports `config_file` / `config_sources` / `primary_api_mode` / `primary_api_mode_source` / `capability_status` / `minimum_profile_ok`, and includes `main_search_connection_tests` plus connection test objects for Exa, Tavily, Zhipu, Context7, and Firecrawl. `primary_connection_test` remains as a backward-compatible alias for the first configured main-search provider check. Firecrawl currently reports whether `FIRECRAWL_API_KEY` is configured; it is not a live Firecrawl request.

Smoke output includes `ok`, `mode`, `failed_cases`, `cases`, `provider_attempts`, and `elapsed_ms`. Live smoke may include `degraded_cases` when a provider fails but a same-capability fallback remains available.

Setup and config output should include `ok` and `config_file`. Saved API keys must be masked in command output.

Interactive setup behavior:

- Default `smart-search setup` shows a Smart Search ASCII banner, asks for `zh`
  or `en`, offers project-local `smart-search-cli` skill installation, then
  shows a grouped provider wizard.
- The grouped wizard should use an arrow-key / Space / Enter selector when the
  packaged TUI dependencies are available, with a text fallback for non-TTY
  and tests.
- Skill installation is project-local only. It installs the bundled
  `smart-search-cli` skill into selected AI-tool skill directories and must not
  run `trellis init`, create hooks, create agents, create commands, or modify
  other skills.
- Skill targets are `codex`, `claude`, `cursor`, `opencode`, `copilot`,
  `gemini`, `kiro`, `qoder`, `codebuddy`, `droid`, `pi`, `kilo`,
  `antigravity`, and `windsurf`. `--skip-skills` disables skill installation.
  `--install-skills codex,claude,cursor` selects targets explicitly, and
  `--skills-root PATH` overrides the project root used for installation.
- Required groups are `main_search`, `docs_search`, and `web_fetch`; `web_search` is optional reinforcement.
- `--lang zh|en` skips the language question.
- `--advanced` shows low-level config keys one by one for compatibility with older setup behavior and does not show the skill prompt unless `--install-skills` is explicit.
- `--non-interactive` keeps script behavior and only saves values passed as flags.
- Unchecking a configured provider must not delete existing config values; use
  `smart-search config unset KEY` for deletion.
- Interactive output should summarize `minimum_profile_ok`, missing required capabilities, and next-step commands.
- Beginner filling examples for official-service and relay/pooled-endpoint
  minimum profiles must appear in the grouped wizard on stderr, not stdout.
  They must cover `main_search`, `docs_search`, and `web_fetch` so a first-time
  user can satisfy the minimum profile without understanding provider internals.

Provider endpoint setup:

- `TAVILY_API_URL` defaults to `https://api.tavily.com`.
- Tavily Hikari / pooled endpoints must use the REST facade base
  `https://<host>/api/tavily`; `/mcp` is not a REST provider base.
- Setup normalizes a Hikari root host or `/mcp` URL to
  `https://<host>/api/tavily`; an existing `/api/tavily` base and official
  `https://api.tavily.com` remain unchanged.
- `FIRECRAWL_API_URL` defaults to `https://api.firecrawl.dev/v2`; custom REST
  bases are saved with scheme normalization and no trailing slash.

Search timeout output uses `ok=false`, `error_type=network_error`, includes the timeout seconds in `error`, keeps `query`, `content`, `sources`, `sources_count`, `primary_sources`, `primary_sources_count`, `extra_sources`, and `extra_sources_count`, and exits with code `4`.

## Provider Routing

- `search` builds `main_search` from peer providers: `XAI_API_KEY` registers xAI Responses, while `OPENAI_COMPATIBLE_API_URL` + `OPENAI_COMPATIBLE_API_KEY` registers OpenAI-compatible Chat Completions.
- Legacy `SMART_SEARCH_API_URL` / `SMART_SEARCH_API_KEY` still work. `SMART_SEARCH_API_MODE=auto` maps `https://api.x.ai/v1` to official xAI Responses API `/responses`; all other URLs map to OpenAI-compatible Chat Completions `/chat/completions`.
- `SMART_SEARCH_API_MODE` may be explicitly set to `xai-responses` or `chat-completions` for the legacy primary endpoint.
- `XAI_TOOLS` or legacy `SMART_SEARCH_XAI_TOOLS` applies only to xAI Responses mode and supports only `web_search` and `x_search`.
- Chat Completions mode must not send xAI `web_search` / `x_search` tools or legacy `search_parameters`; xAI Chat Completions Live Search is deprecated.
- Standard minimum profile requires `main_search`, `docs_search`, and fetch capability. Missing required capabilities produce a configuration error.
- Same-capability fallback is allowed; cross-capability fallback is not. Context7 is not used for unrelated broad web queries, and page extraction providers are not used as docs search providers.
- `main_search`: xAI Responses first for Grok/xAI, then OpenAI-compatible answer fallback when that peer provider is separately configured and `--fallback auto` is active.
- `web_search`: Zhipu first when routed in, then Tavily / Firecrawl source search when configured.
- `docs_search`: Exa first, then Context7.
- Fetch capability: Tavily first, then Firecrawl.
- `search` calls Tavily and/or Firecrawl only when `--extra-sources` is greater than 0.
- If both Tavily and Firecrawl are configured, `search --extra-sources N` gives about 60% of extra source slots to Tavily and the remainder to Firecrawl.
- `extra_sources` are retrieved in parallel and are not automatically used by the primary model to verify its answer.
- `fetch` tries Tavily first, then Firecrawl as fallback when Tavily returns no content.
- `map` uses Tavily only.
- `exa-search` and `exa-similar` use Exa only.
- `zhipu-search` uses Zhipu only.
- `context7-library` and `context7-docs` use Context7 only.
- Runtime config priority is environment variables first, then local config file, then defaults.
- `setup` and `config` read/write the local Smart Search config file and do not call providers.
- `model current` and `model set` read/write the local Smart Search config file and do not call providers.

## Routing Heuristics

- Use `exa-search --include-domains` when official documentation domains are known.
- Use `context7-library` / `context7-docs` for docs/API/SDK/library/framework intent when Context7 is configured.
- Use `zhipu-search` for Chinese, domestic, current, or domain-filtered source discovery when Zhipu is configured.
- Use `exa-search --start-published-date` for recency-constrained source discovery.
- Use `exa-similar` when a known good page is available and adjacent sources are needed.
- Use `search --format content` when a human wants only the generated answer body.
- Use `fetch --format markdown` or `fetch --format content` for user-supplied URLs or when exact page text matters.
- Use `map` before fetching many pages from a documentation site.
- Keep `search --extra-sources` small (`1` to `3`) unless broad coverage is requested.
- For current news or high-risk claims, prefer source discovery plus `fetch`; do not treat broad `search.content` plus `extra_sources` as claim-level verification.

## Maintenance Guardrails

- Provider architecture changes must be verified as distributable CLI behavior, not as behavior that only works because one developer machine has a specific wrapper, shell profile, or local config file.
- Register providers by capability first, then route by intent. Fallback is allowed only within the same capability.
- Keep xAI Responses and OpenAI-compatible as peer `main_search` providers. A failed xAI Responses request may fall back to OpenAI-compatible only when `OPENAI_COMPATIBLE_API_URL` and `OPENAI_COMPATIBLE_API_KEY` are separately configured.
- Do not use Context7 for broad news or generic web facts; do not use Tavily or Firecrawl as documentation semantic-search replacements.
- Standard installs must fail closed unless `main_search`, `docs_search`, and fetch capability each have at least one configured provider.
- After provider-routing changes, run source-checkout regression plus `smart-search smoke --mock --format json`. If live keys were used, run a targeted secret scan for exact key substrings before committing.

## Exit Codes

- `0`: success
- `2`: parameter error
- `3`: configuration error
- `4`: network or upstream error
- `4`: also used for strict insufficient-evidence search failures
- `5`: runtime or parse error

## Regression

Run `smart-search regression` before considering CLI or skill changes complete.

- In a source checkout, it runs offline pytest coverage for CLI, service, smoke, provider, and skill contract behavior.
- In npm / mise packaged installs, repository test files are not bundled; since v0.1.8 it falls back to built-in mock smoke regression so users can still verify installed CLI health.
- For release validation, use a source checkout for full pytest-backed regression and use packaged-install regression only as an install-health check.

## Tool Policy

Web research through this skill should use `smart-search` CLI. If the CLI is unavailable, report the blocker and recovery steps instead of silently falling back to another web-search route.
