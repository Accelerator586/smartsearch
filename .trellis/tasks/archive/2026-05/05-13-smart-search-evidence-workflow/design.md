# Design: Claude/Codex Semantic Discovery + Smart Search Evidence Workflow

## Overview

Change the project messaging and installed skill behavior from an exclusive
`smart-search` routing model to a collaborative workflow:

- Native model reasoning and native web search, when available, are discovery
  tools for planning, query expansion, candidate source discovery, and semantic
  exploration.
- `smart-search` is the evidence layer for provider-routed searches, source
  retrieval, URL fetches, site maps, reproducible JSON/Markdown outputs, and
  final claim support.

This remains CLI-first. The design does not introduce MCP tools, MCP
dependencies, or Claude Code `WebSearch` / `WebFetch` deny-listing.

## Affected Surfaces

- Source skill:
  - `skills/smart-search-cli/SKILL.md`
  - `skills/smart-search-cli/references/cli-contract.md`
  - `skills/smart-search-cli/agents/openai.yaml`
- Packaged skill assets:
  - `src/smart_search/assets/skills/smart-search-cli/SKILL.md`
  - `src/smart_search/assets/skills/smart-search-cli/references/cli-contract.md`
  - `src/smart_search/assets/skills/smart-search-cli/agents/openai.yaml`
- Setup wizard and installation copy:
  - `src/smart_search/cli.py`
- Product documentation:
  - `README.md`
- Tests:
  - `tests/test_regression.py`
  - any CLI/setup tests whose expected copy changes.

## Capability-Extension Contract (Two Axes)

`smart-search` extends native search along **two independent axes**:

- **Semantic-breadth axis** — break out of native search's single-backend
  narrowness via multi-provider routing (Exa neural, Zhipu Chinese/regional,
  Context7 docs/SDK, Tavily, Firecrawl, xAI Responses, OpenAI-compatible),
  `exa-similar` semantic neighbors, `map` domain topology, and
  cross-language/cross-region coverage.
- **Evidence-depth axis** — produce auditable, reproducible answers via
  provider-routed retrieval with preserved command lines, source URLs,
  fetched page text or `primary_sources`, and stable JSON/Markdown.

The two axes are independent. Engaging the extension for semantic breadth
does not impose the audit hard constraint; engaging it for evidence depth
does.

The skill body is rewritten as three prose sections that frame
`smart-search` as a dual-axis extension of native search, not as a separate
workflow track:

1. **Baseline search**
   - Native reasoning and, when available, native web search are the AI's
     baseline.
   - Baseline is the default for casual lookups, query planning, alias
     discovery, version names, and shaping the search space.
   - Flag two known limits of baseline so the AI does not silently fall
     into either: it can be **semantically narrow** (single backend,
     single language, single index), and it does not produce **auditable**
     evidence.

2. **Where baseline isn't enough (heuristic signals on two axes)**
   - Written as prose principles, not a numbered enumeration of triggers.
   - **Semantic-breadth signals**: native results look narrow / biased /
     single-language / single-source; the query needs neighbors of a seed
     URL; a documentation domain's structure matters; coverage across
     Chinese / regional / academic indices matters; the AI suspects native
     search has anchored its mental model too quickly.
   - **Evidence-depth signals**: claim needs cited sources; official
     docs / API / SDK research; current / high-risk data (news / policy /
     finance / health); user-supplied URLs; multi-source comparison; site
     mapping; the user asks for verification, audit, or reproducibility.
   - Wording: "where baseline search isn't enough" / "when broader semantic
     coverage or stronger evidence is needed" — never "escalate to a
     different workflow."

3. **`smart-search` as the dual-axis extension**
   - `smart-search` is positioned as the upgrade applied to search when
     section 2 signals are present. Same activity (searching the web),
     performed with broader providers and/or auditable outputs.
   - **Provider-to-axis map** (skill body should communicate this so the AI
     picks the right command per axis):
     - Breadth-leaning: `exa-search` (neural/academic),
       `zhipu-search` (Chinese/domestic), `context7-library` /
       `context7-docs` (SDK/library specialized), `exa-similar` (semantic
       neighbors), `map` (domain topology).
     - Depth-leaning: `fetch` (exact page text), `primary_sources` from
       `search` / `exa-search`, `--output` saved evidence files,
       provider-routed `search` with the existing fallback contract.
     - Many commands serve both axes; the mapping is about emphasis, not
       exclusivity.
   - Prefer fetched text or `primary_sources` for final claims.
   - `extra_sources` are candidates until fetched or otherwise verified, and
     never constitute audit evidence on their own.
   - **Audit hard constraint (scoped to the evidence-depth axis)**: when
     the answer rests on smart-search results as evidence, the final
     answer must preserve smart-search command lines, the source URLs, and
     either fetched-page text or `primary_sources`. Breadth-only uses that
     do not back final claims (e.g., exploratory neighbor lookups that
     the AI then discards) are not subject to this constraint.

Concrete command examples are kept, but demoted to a small "Command
Reference" section at the end of `SKILL.md` (5–8 representative commands)
plus a link to `references/cli-contract.md`. The three prose sections above
must read as a capability-extension explainer, not as a feature catalog and
not as a two-phase workflow.

### `agents/openai.yaml` Lock

Source skill (`skills/smart-search-cli/agents/openai.yaml`) and packaged copy
(`src/smart_search/assets/skills/smart-search-cli/agents/openai.yaml`) must
use:

```yaml
display_name: Smart Search Evidence Extension
short_description: Extends native search along two axes — semantic breadth (multi-provider, cross-language, neighbors, site maps) and evidence depth (cited URLs, audit-grade, reproducible). Use only when baseline search is too narrow or the answer needs citations.
default_prompt: Apply $smart-search-cli to widen the semantic field and/or back this answer with cited, reproducible sources.
```

Regression tests should assert at least `Smart Search Evidence Extension` in
`display_name` and the phrase `use only when` in `short_description` to lock
the gate against drift back to a generic-search framing.

### Frontmatter Description (Strict Invocation Gate)

`SKILL.md`'s frontmatter `description` is what AI tools read **before** loading
the skill body, and it gates whether the skill is invoked at all. Under the
extension framing, the description must:

- Open with the canonical name `Smart Search Evidence Extension`.
- State explicitly that this is an *extension of native search* along **two
  axes** (semantic breadth + evidence depth), not a default search route.
- Enumerate, as prose, signals on **both** axes that warrant invocation:
  semantic-breadth signals (narrow/biased/single-language native results,
  Chinese / regional / academic coverage, neighbors of a seed URL,
  documentation domain structure) and evidence-depth signals (cited URLs,
  official docs/API, current/high-risk data, user-supplied URLs,
  audit/reproducibility).
- State explicitly that casual lookups native search can already answer should
  **not** invoke this skill.

The implementer should draft an English string consistent with the above
intent; regression tests should assert (at minimum) the canonical name and a
phrase that conveys the "skip for casual lookups" gate.

### Content migration (SKILL.md → cli-contract.md)

The following heavy content moves out of `SKILL.md` and into
`references/cli-contract.md`, which already covers Entrypoints, Commands,
and Aliases. Migration is additive, not replacing the existing reference
content:

- Full **Provider Routing** rules (the ~21 bullets currently in `SKILL.md`):
  appended to `cli-contract.md` as a new "Provider Routing" section.
- **Local wrapper contract** bullets (PATH, sandbox `SMART_SEARCH_CONFIG_DIR`,
  Tavily / Firecrawl base URLs, setup wizard contract): appended to
  `cli-contract.md` as a new "Local Wrapper Contract" section.
- **Command Patterns** full table: stays in `cli-contract.md` (already
  partially present); `SKILL.md` keeps only 5–8 representative commands.

Target `SKILL.md` length after restructure: roughly 70–90 lines.

`SKILL.md` retains:

- Capability-extension framing and canonical name
  (`Smart Search Evidence Extension` / `Smart Search 扩展`).
- The three prose sections (Baseline / Where baseline isn't enough /
  Smart Search as Evidence Extension).
- Audit hard constraint.
- A compact "Command Reference" with 5–8 representative commands.
- Extension-specific Guardrails (JSON for agents, `--output` for citation
  work, `extra_sources` not proof, no MCP tool names).
- A single pointer line to `references/cli-contract.md` for full details.

## Copy and Policy Changes

Remove or rewrite current exclusive phrasing:

- "Use the local `smart-search` command as the default execution layer for web
  research" should become "Use `smart-search` as the reproducible evidence
  layer when a task needs source-backed or auditable research."
- "Do not call Codex native web search in the same task" should be removed.
- "native `web_search` is disabled" should be removed.
- "do not silently fall back to native web search" should be reframed:
  when `smart-search` is selected for evidence work and fails, report the
  failure and recovery steps instead of using unverifiable results as evidence.

Keep existing evidence guardrails:

- JSON for agent parsing.
- Markdown for fetched page text.
- `--output` for multi-source or citation-heavy work.
- `extra_sources` are not proof.
- Fetch exact pages for claim-level support.
- Same-capability provider fallback remains a service-level behavior.

## Asset Synchronization

The repo currently keeps source skills under `skills/` and packaged copies
under `src/smart_search/assets/skills/`. This task should keep them identical
for changed files.

Implementation can either edit both copies manually or copy the source skill
tree into the packaged asset tree after edits. Tests should continue to verify
installed skill behavior.

## Tests

Update tests that currently enforce the old exclusive contract:

- `tests/test_regression.py` should assert the new collaborative contract,
  including phrases for semantic discovery and reproducible evidence.
- It should no longer require "native web search is disabled".
- It should still prevent MCP-specific tool naming in the installed skill,
  unless the phrase is part of explaining non-goals. Prefer avoiding old MCP
  tool names entirely in the skill.

If setup copy tests assert old text such as "call the smart-search CLI first",
update them to the collaborative wording.

## Compatibility

- Existing CLI command names, aliases, output schemas, provider routing, config
  keys, and package entrypoints remain unchanged.
- Codex and Claude Code install target paths remain unchanged.
- No MCP dependency or entrypoint is added.

## Rollback

This change is largely documentation/skill-copy behavior. Rollback means
restoring the previous skill/README/setup copy and the old regression
expectations. No user config migration is required.
