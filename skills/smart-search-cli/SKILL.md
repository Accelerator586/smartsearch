---
name: smart-search-cli
description: CLI-first web research and source retrieval through the local smart-search command. Use when Codex needs current web search, source-backed fact checking, URL fetching, site mapping, official/API/documentation search, or reproducible search evidence via Skill + CLI instead of MCP tools.
---

# Smart Search CLI

Use the local `smart-search` command as the default execution layer for web research. The skill decides routing; the CLI performs the work; JSON or saved files provide evidence.

## Default workflow

1. Run `smart-search doctor --format json` when configuration or availability is uncertain.
2. If `doctor` reports missing configuration, use `smart-search setup` or `smart-search config set KEY VALUE` when the user provides keys. Do not ask users to edit global environment variables by default.
3. If `doctor` returns `ok: true`, use only `smart-search` CLI subcommands for web research. Do not call Codex native web search in the same task.
4. Use `smart-search smoke --mock --format json` after CLI/provider architecture changes. Use `--live` only when real keys are available and the user expects live checks.
5. Use `smart-search search` for realtime, broad, community, or multi-source synthesis.
6. Use `smart-search exa-search` for official documentation, API references, papers, and low-noise source discovery.
7. Use `smart-search context7-library` / `context7-docs` only for library, SDK, API, framework, or documentation intent.
8. Use `smart-search zhipu-search` for Chinese, domestic, current, or domain-filtered web source discovery.
9. Use `smart-search exa-similar` when the user gives a representative URL and wants related pages or neighboring sources.
10. Use `smart-search fetch` when the user gives a URL or a claim depends on page content.
11. Use `smart-search map` when a documentation site or domain structure matters.
12. Use `smart-search model current` or `model set` only for explicit model checks or changes.
13. For current-news, policy, finance, health, or other high-risk facts, do not answer from broad `search.content` alone. Find reliable URLs with `exa-search`, `zhipu-search`, or source-focused `search`, then `fetch` key pages and summarize only what the fetched text supports.
14. Preserve command lines and source URLs in your answer. Prefer citing fetched pages or `primary_sources`; treat `extra_sources` as follow-up candidates, not verified evidence for generated claims.

## Provider Routing

- `search` builds `main_search` from configured peer providers: `XAI_API_KEY` for xAI Responses and `OPENAI_COMPATIBLE_API_URL` + `OPENAI_COMPATIBLE_API_KEY` for OpenAI-compatible Chat Completions.
- Legacy `SMART_SEARCH_API_URL` / `SMART_SEARCH_API_KEY` still work: `https://api.x.ai/v1` resolves to xAI Responses, other URLs resolve to OpenAI-compatible Chat Completions.
- xAI Responses mode may use only `XAI_TOOLS=web_search,x_search` or `SMART_SEARCH_XAI_TOOLS=web_search,x_search` and a subset of those tools.
- Chat Completions mode must not send xAI `web_search` / `x_search` tools or legacy `search_parameters`; xAI Chat Completions Live Search is deprecated.
- The standard minimum profile requires one configured provider in each of `main_search`, `docs_search`, and fetch capability. Missing required capabilities should be treated as a hard configuration failure.
- `search` exposes `--validation fast|balanced|strict`, `--fallback auto|off`, and `--providers auto|CSV`. Default validation is `balanced`; fallback only happens within the same capability.
- xAI Responses is the default main answer route for Grok/xAI. In `fallback=auto`, a failed xAI Responses main route can fall back to OpenAI-compatible only when the OpenAI-compatible provider is separately configured.
- Docs routing uses Exa first, then Context7 only for docs/API/SDK/library/framework intent.
- Zhipu is a general web-search reinforcement and same-capability fallback for Chinese, domestic, current, or domain-filtered source discovery.
- `search` calls Tavily and/or Firecrawl only when `--extra-sources N` is greater than 0.
- With both Tavily and Firecrawl configured, `search --extra-sources N` splits extra sources between them, with Tavily receiving about 60% and Firecrawl the rest.
- Search JSON separates `primary_sources`, `extra_sources`, and backward-compatible merged `sources`.
- `primary_sources` are extracted from the primary model answer. `extra_sources` are parallel Tavily / Firecrawl candidates and are not automatically used to verify `content`.
- `fetch` tries Tavily first and uses Firecrawl only as a fallback when Tavily returns no content.
- `map` currently uses Tavily only.
- `exa-search` and `exa-similar` use Exa only.
- `context7-library` and `context7-docs` use Context7 only.
- `zhipu-search` uses Zhipu only.
- `doctor` tests configured main-search providers, Exa, Tavily, Zhipu, and Context7 connectivity. Firecrawl status currently means the key is configured, not that a live Firecrawl request succeeded.

## Evidence Files

For multi-source research, use `--output` to save evidence under `C:\tmp\smart-search-evidence\` with a descriptive timestamped filename. Stdout should still contain the full JSON result unless markdown was explicitly chosen for human reading.

For claim-level evidence, prefer this order:

1. Discover candidate URLs with `exa-search` or source-focused `search`.
2. Fetch the exact pages that matter.
3. Use broad `search` only as synthesis or discovery, and mark claims as unverified when only `extra_sources` are available.

Prefer shorter, source-directed commands:

```powershell
smart-search exa-search "Reuters Iran Hormuz latest" --num-results 5 --include-highlights --format json --output C:\tmp\smart-search-evidence\iran-hormuz-exa.json
smart-search exa-search "OpenAI Responses API documentation" --include-domains platform.openai.com,developers.openai.com --num-results 5 --include-text --format json
smart-search exa-similar "https://example.com/source" --num-results 5 --format json
smart-search fetch "https://example.com/source" --format json --output C:\tmp\smart-search-evidence\source-fetch.json
smart-search search "Iran Hormuz latest military talks" --extra-sources 3 --timeout 90 --format json --output C:\tmp\smart-search-evidence\iran-hormuz-search.json
```

## Local wrapper contract

- Expect `smart-search` to resolve from the user's PATH.
- This bundled skill is maintained with the `smartsearch` repository.
- Prefer the CLI's local config file managed by `smart-search setup` / `smart-search config`.
- Environment variables remain supported for CI and advanced users, and override the local config file.
- Do not ask users to set Windows global API-key environment variables by default.
- If keys are changed with `smart-search config set`, rerun the CLI; no Codex restart is needed.
- If PATH is changed, a new terminal or Codex restart may be needed.
- In sandboxed runtimes (Codex CLI, containers, CI) where the user's home directory may not be writable from spawned subprocesses, set `SMART_SEARCH_CONFIG_DIR` to an absolute path the runtime can write to. The CLI uses it for both config and logs and skips home-directory fallback.
- If `smart-search doctor --format json` returns `ok: false`, follow the `error` field's guidance (`smart-search setup` or `smart-search config set KEY VALUE`); do not silently fall back to native web search.

## Command Patterns

```powershell
smart-search search "query" --extra-sources 5 --timeout 90 --format json --output result.json
smart-search search "query" --platform "Reuters" --model "model-id" --extra-sources 3 --timeout 90 --format json
smart-search search "query" --validation strict --fallback auto --providers auto --format json
smart-search exa-search "query" --num-results 5 --search-type neural --include-text --include-highlights --include-domains docs.example.com --format json
smart-search exa-similar "https://example.com/article" --num-results 5 --format json
smart-search context7-library "react" "hooks" --format json
smart-search context7-docs "/facebook/react" "useEffect cleanup" --format json
smart-search zhipu-search "today China AI news" --count 5 --format json
smart-search fetch "https://example.com" --format markdown --output page.md
smart-search map "https://docs.example.com" --instructions "Find API reference pages" --max-depth 1 --max-breadth 20 --limit 50 --format json
smart-search setup
smart-search config path --format json
smart-search config list --format json
smart-search config set SMART_SEARCH_API_MODE "xai-responses" --format json
smart-search config set SMART_SEARCH_XAI_TOOLS "web_search,x_search" --format json
smart-search config set EXA_API_KEY "key" --format json
smart-search config set CONTEXT7_API_KEY "key" --format json
smart-search config set ZHIPU_API_KEY "key" --format json
smart-search model current --format json
smart-search model set "model-id" --format json
smart-search doctor --format json
smart-search regression
smart-search smoke --mock --format json
```

## Guardrails

- Prefer JSON for agent parsing and markdown for fetched page text intended for reading.
- Use `--output` for multi-source work, long pages, or anything the answer may need to cite later.
- Keep `--extra-sources` small (`1` to `3`) unless the user asks for broad coverage. Large values are slower and can add noise.
- Do not cite `extra_sources` as proof for a sentence in `content`; fetch the URL first or cite it only as a candidate source.
- Prefer `exa-search --include-domains` for official documentation when likely domains are known.
- Do not expose API keys. Treat `doctor` output as safe only because it is expected to mask secrets.
- In this CLI-first workflow, native `web_search` is disabled unless the user explicitly configures another approved route.
- If `doctor` or a command fails, report the failure and recovery steps; do not silently fall back to another web-search route.
- If the user explicitly asks to bypass smart-search, state that another approved web-search route must be configured first.
- Do not use legacy MCP tool names in prompts, notes, or generated instructions for this workflow.
- Treat key rotation as a hard safety gate when previous key values were pasted into chat or logs.
- For provider architecture maintenance, verify the distributable contract rather than the current developer machine's wrappers or local config. Keep fallback same-capability only.
- Treat xAI Responses and OpenAI-compatible as peer `main_search` providers. Do not reuse one provider's URL/key to fabricate the other provider as a fallback.

## Supporting Reference

Read `references/cli-contract.md` when you need command details, output fields, exit codes, or regression expectations.
