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
4. Use `smart-search search` for realtime, broad, community, or multi-source synthesis.
5. Use `smart-search exa-search` for official documentation, API references, papers, and low-noise source discovery.
6. Use `smart-search exa-similar` when the user gives a representative URL and wants related pages or neighboring sources.
7. Use `smart-search fetch` when the user gives a URL or a claim depends on page content.
8. Use `smart-search map` when a documentation site or domain structure matters.
9. Use `smart-search model current` or `model set` only for explicit model checks or changes.
10. For complex current-news work, split the task: run targeted `exa-search` queries, fetch key URLs, then optionally run a short `search` synthesis. Avoid one long all-purpose query.
11. Preserve command lines and source URLs in your answer. Cite URLs from `sources` or result records.

## Provider Routing

- `search` uses the primary OpenAI-compatible endpoint. It calls Tavily and/or Firecrawl only when `--extra-sources N` is greater than 0.
- With both Tavily and Firecrawl configured, `search --extra-sources N` splits extra sources between them, with Tavily receiving about 60% and Firecrawl the rest.
- `fetch` tries Tavily first and uses Firecrawl only as a fallback when Tavily returns no content.
- `map` currently uses Tavily only.
- `exa-search` and `exa-similar` use Exa only.
- `doctor` tests the primary endpoint, Exa, and Tavily connectivity. Firecrawl status currently means the key is configured, not that a live Firecrawl request succeeded.

## Evidence Files

For multi-source research, use `--output` to save evidence under `C:\tmp\smart-search-evidence\` with a descriptive timestamped filename. Stdout should still contain the full JSON result unless markdown was explicitly chosen for human reading.

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

## Command Patterns

```powershell
smart-search search "query" --extra-sources 5 --timeout 90 --format json --output result.json
smart-search search "query" --platform "Reuters" --model "model-id" --extra-sources 3 --timeout 90 --format json
smart-search exa-search "query" --num-results 5 --search-type neural --include-text --include-highlights --include-domains docs.example.com --format json
smart-search exa-similar "https://example.com/article" --num-results 5 --format json
smart-search fetch "https://example.com" --format markdown --output page.md
smart-search map "https://docs.example.com" --instructions "Find API reference pages" --max-depth 1 --max-breadth 20 --limit 50 --format json
smart-search setup
smart-search config path --format json
smart-search config list --format json
smart-search config set EXA_API_KEY "key" --format json
smart-search model current --format json
smart-search model set "model-id" --format json
smart-search doctor --format json
smart-search regression
```

## Guardrails

- Prefer JSON for agent parsing and markdown for fetched page text intended for reading.
- Use `--output` for multi-source work, long pages, or anything the answer may need to cite later.
- Keep `--extra-sources` small (`1` to `3`) unless the user asks for broad coverage. Large values are slower and can add noise.
- Prefer `exa-search --include-domains` for official documentation when likely domains are known.
- Do not expose API keys. Treat `doctor` output as safe only because it is expected to mask secrets.
- In this CLI-first workflow, native `web_search` is disabled unless the user explicitly configures another approved route.
- If `doctor` or a command fails, report the failure and recovery steps; do not silently fall back to another web-search route.
- If the user explicitly asks to bypass smart-search, state that another approved web-search route must be configured first.
- Do not use legacy MCP tool names in prompts, notes, or generated instructions for this workflow.
- Treat key rotation as a hard safety gate when previous key values were pasted into chat or logs.

## Supporting Reference

Read `references/cli-contract.md` when you need command details, output fields, exit codes, or regression expectations.
