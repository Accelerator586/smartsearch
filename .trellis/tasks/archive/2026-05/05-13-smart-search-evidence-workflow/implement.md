# Implementation Plan

## Pre-flight

- [x] Refresh development guidelines with `trellis-before-dev` before editing.
- [x] Re-read `prd.md` (Workflow Principles, Canonical Naming) and `design.md`
      (Capability-Extension Contract, `agents/openai.yaml` Lock, Frontmatter
      Description, Content Migration) so all four user-facing surfaces stay
      consistent.

## Skill source: `skills/smart-search-cli/`

- [x] Rewrite `SKILL.md` frontmatter `description` to the strict-gate form:
  - opens with `Smart Search Evidence Extension`;
  - states this is an extension of native search, not a default search route;
  - lists evidence-grade signals (cited URLs, official docs/API,
    current/high-risk data, user-supplied URLs, audit/reproducibility);
  - explicitly states casual lookups should not invoke the skill.
- [x] Rewrite `SKILL.md` body as three prose sections, dual-axis framing:
  1. Baseline search (native default) — flag both limits of baseline:
     semantically narrow + non-auditable.
  2. Where baseline isn't enough — split into two signal families
     (semantic-breadth signals + evidence-depth signals), prose, not
     enumeration.
  3. Smart Search as the **dual-axis** extension — include the
     provider-to-axis mapping (breadth-leaning vs depth-leaning commands)
     and the audit hard constraint scoped to the evidence-depth axis.
- [x] In section 3, state the audit hard constraint explicitly using the
      anchor terms `preserve`, `command line`, `primary_sources`, `fetched`,
      and that `extra_sources` alone are not evidence. Make explicit that
      the constraint applies only when the extension's results back the
      final answer (evidence-depth axis engaged).
- [x] In sections 2 and 3, include at least one semantic-breadth anchor
      (e.g., `narrow`, `single-language`, `multi-provider`, `Chinese`,
      `neighbors`) so the breadth axis cannot disappear in future edits.
- [x] Use canonical naming throughout: `Smart Search Evidence Extension` in
      English headings/prose; `Smart Search 扩展` does not appear in
      `SKILL.md` (English-only file).
- [x] Remove all exclusive-policy phrases:
  - `native web search is disabled`;
  - `Do not call Codex native web search in the same task`;
  - `do not silently fall back to native web search`;
  - any "use smart-search as the default execution layer" wording.
- [x] Keep a compact "Command Reference" section at the end with 5–8
      representative commands (cover `search`, `exa-search`, `zhipu-search`,
      `context7-docs`, `fetch`, `map`, `doctor`).
- [x] Add a single pointer line to `references/cli-contract.md` for full
      details (commands, aliases, provider routing, local wrapper contract).
- [x] Keep extension-specific Guardrails (JSON for agent parsing, `--output`
      for citation work, `extra_sources` are not proof, no legacy MCP tool
      names, key rotation gate). Drop guardrails that restate native-search
      disablement.
- [x] Target `SKILL.md` length: 70–90 lines.

- [x] Update `references/cli-contract.md` (additive, not replacing existing
      Entrypoints / Commands / Aliases):
  - append a new **Provider Routing** section absorbing the ~21 routing
    bullets currently in `SKILL.md` (xAI Responses vs Chat Completions,
    docs routing, Zhipu reinforcement, Tavily/Firecrawl extra-source split,
    `doctor` coverage, fallback rules);
  - append a new **Local Wrapper Contract** section absorbing PATH /
    `SMART_SEARCH_CONFIG_DIR` / setup-wizard / Tavily-Firecrawl base URL
    bullets currently in `SKILL.md`.

- [x] Update `agents/openai.yaml` to the locked dual-axis values:
  ```yaml
  display_name: Smart Search Evidence Extension
  short_description: Extends native search along two axes — semantic breadth (multi-provider, cross-language, neighbors, site maps) and evidence depth (cited URLs, audit-grade, reproducible). Use only when baseline search is too narrow or the answer needs citations.
  default_prompt: Apply $smart-search-cli to widen the semantic field and/or back this answer with cited, reproducible sources.
  ```

## Packaged skill asset sync

- [x] After source edits, sync the three changed files into
      `src/smart_search/assets/skills/smart-search-cli/`:
  - `SKILL.md`
  - `references/cli-contract.md`
  - `agents/openai.yaml`
- [x] Confirm `diff -q skills/smart-search-cli/ src/smart_search/assets/skills/smart-search-cli/`
      reports no content differences.

## Setup wizard and README

- [x] Update `src/smart_search/cli.py` skill-install prompt (currently around
      lines 597–598) so both Chinese and English copy describe skill
      installation as adding the **Smart Search Evidence Extension** /
      **Smart Search 扩展**, not as routing all web research through the CLI.
      Remove any "call the smart-search CLI first" or
      "let AI tools call smart-search first" framing.
- [x] Update `README.md` skill-injection paragraphs in both Chinese
      (~line 146) and English (~line 612) sections:
  - introduce the canonical name once in each language;
  - describe installation as teaching AI tools an evidence extension, not as
    forcing all web research through `smart-search`;
  - keep references to supported install targets (Codex, Claude Code,
    Cursor, OpenCode, GitHub Copilot, etc.) unchanged.

## Tests

- [x] Rewrite `tests/test_regression.py::test_smart_search_skill_contract_enforces_cli_first`
      (rename function to reflect the new contract, e.g.
      `test_smart_search_skill_contract_enforces_evidence_extension`):
  - **Required positive anchors** (must appear in skill text):
    `Smart Search Evidence Extension`, `preserve`, `command line`,
    `primary_sources`, `fetched`. Additionally at least one
    semantic-breadth anchor from
    `{narrow, single-language, multi-provider, Chinese, neighbors}` must
    appear, and at least one dual-axis anchor from
    `{semantic, breadth}` plus `{evidence, audit}` must both appear so
    neither axis can be silently dropped.
  - **Forbidden phrases** (must NOT appear in skill text):
    `native web search is disabled`,
    `Do not call Codex native web search`,
    `do not silently fall back to native web search`,
    `default execution layer for web research`.
  - **`agents/openai.yaml` checks**: `display_name` equals
    `Smart Search Evidence Extension`; `short_description` contains
    `use only when`.
  - **`extra_sources` claim**: assert that the skill text does not state or
    imply `extra_sources` alone constitute audit evidence; treat any
    sentence pairing `extra_sources` with `evidence`/`proof` without a
    negation as a failure.
- [x] Update any `tests/test_cli.py` assertions that reference the old
      skill-install copy (zh/en strings around the skill prompt) to match the
      new wording. Use a substring check on a short anchor, not exact full-
      copy match, to keep the test resilient.
- [x] Run focused tests:
  - `python3 -m pytest tests/test_regression.py tests/test_cli.py` (51 passed)
- [x] Run full offline regression if focused tests pass:
  - `python3 -m pytest` (87 passed, 47 skipped — async tests require pytest-asyncio, pre-existing)
  - or `smart-search regression` if local command resolution is available.
- [ ] Run `smart-search smoke --mock --format json` if CLI command is
      available after changes. _(skipped: `smart-search` not on PATH; per Validation Notes, Python test coverage substitutes)_

## Risk Points

- Source skill (`skills/`) and packaged copy
  (`src/smart_search/assets/skills/`) drift: explicitly diff after edits.
- Tests currently expect old exclusive wording — replace, don't append, so
  the contract actually shifts.
- README is bilingual; Chinese and English copy must stay semantically
  aligned but use canonical names in their own languages
  (`Smart Search Evidence Extension` / `Smart Search 扩展`).
- The frontmatter `description` is the AI-tool invocation gate; if it
  reads too generic, the extension will be loaded for every web question
  and the framing collapses back to "default search route."

## Validation Notes

- No live provider keys are required for the expected test path.
- Do not add `fastmcp`, MCP entrypoints, Claude Code deny-list behavior, or
  new provider config semantics.
- Do not change CLI default behavior (e.g., do not force `--output` on by
  default); the audit hard constraint is enforced through skill copy and
  tests, not through CLI runtime changes.
- If local `smart-search` is not on PATH during validation, report that and
  rely on Python test coverage.

## Sub-agent Mode

This task is treated as **lightweight in-context implementation**: PRD +
design + this checklist contain enough context, and `implement.jsonl` /
`check.jsonl` need no spec/research entries beyond placeholders. Re-evaluate
if execution actually requires sub-agent dispatch; in that case, curate the
manifests before `task.py start`.

## Boundary Calibration (added 2026-05-14 via brainstorm)

These items refine the in-progress implementation after the first edit pass
revealed gaps against the original design. They take precedence over earlier
identical items if there is overlap.

- [x] **Strengthen `extra_sources` regression contract.** Inside
      `_assert_evidence_extension_contract` (`tests/test_regression.py`), add a
      negation-aware check that fails when a sentence in the combined skill
      text pairs `extra_sources` with `evidence` or `proof` **without** a
      neighboring negation token (e.g., `not`, `never`, `alone never`,
      `do not`). Implementation hint: split skill text by sentence-ending
      punctuation, scan each sentence containing `extra_sources`, fail when it
      also contains `evidence` / `proof` and lacks any negation token. SKILL.md's
      current wording ("`extra_sources` alone never constitute audit evidence")
      must pass.

- [x] **Add dedicated `## Local Wrapper Contract` section to
      `skills/smart-search-cli/references/cli-contract.md`** (and packaged
      copy). Absorb the bullets that previously lived in the old `SKILL.md`'s
      `Local wrapper contract` section and are not already in `Entrypoints`:
  - "Do not ask users to set Windows global API-key environment variables by
    default."
  - "If keys are changed with `smart-search config set`, rerun the CLI; no
    Codex restart is needed."
  - "If PATH is changed, a new terminal or Codex restart may be needed."
  - Setup wizard contract: language-selecting grouped wizard, arrow-key /
    Space / Enter, walks through `main_search` / `docs_search` / fetch /
    optional `web_search` reinforcement; beginner filling examples on stderr.
  - `smart-search setup --lang en` for English wizard; `--advanced` only when
    low-level keys must be shown.
  - `TAVILY_API_URL=https://<host>/api/tavily` for Tavily Hikari / pooled
    endpoints; setup normalizes root host and `/mcp` inputs.
  - `FIRECRAWL_API_URL` must be a Firecrawl-compatible REST base; official
    default is `https://api.firecrawl.dev/v2`.
- [x] After adding, re-sync to
      `src/smart_search/assets/skills/smart-search-cli/references/cli-contract.md`
      and re-run `diff -q`.

- [x] **Trim `SKILL.md` back into the 70–90 line target** by sinking two
      generic security guardrails from the `Guardrails` section into
      `cli-contract.md`'s `Maintenance Guardrails` section (or the new
      `Local Wrapper Contract` section, whichever fits):
  - "Do not expose API keys. Treat `doctor` output as safe only because it
    masks secrets."
  - "Treat key rotation as a hard safety gate if prior key values were pasted
    into chat or logs."
  - `SKILL.md`'s `Guardrails` section should retain only extension-specific
    items: JSON for agent parsing, `--output` for citation work,
    `--extra-sources` size guidance, `extra_sources` not proof,
    `exa-search --include-domains` for official docs, legacy MCP tool name ban.
  - Target post-trim length: 88–90 lines.

- [x] **Promote Canonical Naming as the `test_cli.py` anchor.** Replace the
      weak substring `"Install the smart-search-cli skill"` at
      `tests/test_cli.py:595` with `"Smart Search Evidence Extension"`
      (English `--lang en` path). For Chinese setup paths in the same file,
      add an additional assertion that captured stderr contains
      `"Smart Search 扩展"`. Both anchors are the load-bearing canonical
      names from `prd.md` "Canonical Naming"; they catch a copy regression
      that the current substring cannot.

## Boundary Calibration Validation

- [x] After the four calibration items above are implemented, re-run
      `python3 -m pytest tests/test_regression.py tests/test_cli.py` and
      confirm the new assertions pass. _(51 passed)_
- [x] Re-confirm `diff -q skills/smart-search-cli/ src/smart_search/assets/skills/smart-search-cli/`
      reports no content differences. _(clean)_
- [x] Re-check `wc -l skills/smart-search-cli/SKILL.md` is within 70–90. _(89 lines)_
