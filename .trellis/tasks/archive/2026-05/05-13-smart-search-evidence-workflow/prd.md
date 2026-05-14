# Claude and Codex smart-search evidence workflow

## Goal

Establish a product and skill workflow where Claude Code and Codex use their
native semantic search/planning strengths together with `smart-search` as the
reproducible evidence layer.

The project should no longer position `smart-search-cli` as an exclusive
replacement for native web search. Instead, it should teach AI tools to use a
two-stage research workflow:

1. Native model reasoning and, when available, native web search are used for
   semantic discovery: search planning, query expansion, finding candidate
   domains, identifying aliases, and exploring the shape of the information
   space.
2. `smart-search` is used for evidence hardening: provider-routed search,
   source discovery, URL fetches, site maps, reproducible JSON/Markdown output,
   and final claim support.

The result should work for both Claude Code and Codex skill installs without
requiring MCP compatibility or deny-listing Claude Code `WebSearch` /
`WebFetch`.

## User Value

- Users keep Claude Code / Codex native capabilities for broad semantic
  discovery instead of disabling them.
- Users gain a clear, repeatable escalation path from exploration to
  verifiable evidence.
- Final answers become easier to audit because `smart-search` commands,
  sources, and fetched page content are preserved when evidence matters.
- The project stays aligned with the CLI-first direction and avoids reintroducing
  MCP context overhead.

## Workflow Principles

These four principles are the load-bearing decisions for this task. All skill
copy, README, setup wizard, agent prompts, and tests must stay consistent with
them.

1. **Heuristic escalation, not hard rules.** The skill should not enumerate a
   rigid "must escalate" trigger list as commands. It should give the AI
   principles and cues ("if the claim needs current/auditable/source-backed
   evidence, escalate") so the AI judges per situation. Trigger examples are
   illustrative, not exhaustive.

2. **`smart-search` extends native search along TWO independent axes, not
   one.** Native search is the AI's baseline. `smart-search` is not a
   parallel workflow track and not a replacement; it is an extension
   applied along either or both of the following axes:

   - **Semantic-breadth axis** — multi-provider routing (Exa neural/academic,
     Zhipu Chinese/regional, Context7 docs/SDK, Tavily, Firecrawl, xAI
     Responses, OpenAI-compatible), `exa-similar` semantic neighbors, `map`
     domain topology, and cross-language/cross-region coverage. Native
     search tends to a single backend and can quietly narrow the AI's
     semantic field; this axis exists specifically to break that
     narrowness.
   - **Evidence-depth axis** — provider-routed retrieval with auditable
     command lines, source URLs, fetched page text or `primary_sources`,
     and reproducible JSON/Markdown across runs.

   The two axes are independent: the AI may invoke `smart-search` for
   semantic breadth alone (exploration that native is too narrow for),
   evidence depth alone (a single claim needs an auditable source), or
   both. The audit hard constraint (principle #4) applies **only when the
   evidence-depth axis is engaged**, not whenever the extension is used.

3. **The skill is a capability-extension document, not a workflow document.**
   It tells the AI: "you already know how to search; here is how to upgrade
   your search along two axes — semantic breadth and evidence depth — when
   the situation calls for it." The skill must not read as "follow this
   two-phase workflow." Concrete commands exist as the toolkit that delivers
   the upgrade, not as workflow steps.

4. **Audit trail is a hard constraint on the evidence path.** Once the AI has
   escalated to `smart-search` for evidence, the resulting answer MUST preserve
   the smart-search command line(s), provider routing chosen, source URLs, and
   either fetched-page text or `primary_sources`. `extra_sources` alone are not
   audit evidence. On the native-only exploration path (no evidence required),
   no audit trail is mandated.

## Canonical Naming

All user-facing artifacts must refer to this capability extension by a
consistent name:

- English: `Smart Search Evidence Extension`
- Chinese: `Smart Search 扩展`

This name appears in `SKILL.md`, packaged skill copies,
`agents/openai.yaml`, README (both `zh` and `en` sections), setup wizard
copy, and is asserted by regression tests as a required anchor phrase. The
name positions `smart-search` as an extension of native search rather than
as a separate workflow or replacement.

## Confirmed Facts

- `smart-search` is a CLI-first project. The primary entrypoint is
  `smart-search`, not an MCP server.
- The bundled `smart-search-cli` skill is installed into project-local AI tool
  skill directories, including Codex `.agents/skills` and Claude Code
  `.claude/skills`.
- Current skill text says that when `doctor` is OK, agents should use only
  `smart-search` CLI subcommands and should not call native web search in the
  same task.
- Current skill guardrails say native `web_search` is disabled unless another
  approved route is configured.
- Tests currently assert the old exclusive wording or policy shape for the
  installed skill.
- `smart-search` already supports evidence-oriented commands and outputs:
  `search`, `fetch`, `map`, `exa-search`, `exa-similar`, `zhipu-search`,
  `context7-library`, `context7-docs`, JSON/Markdown output, `--output`, and
  separate `primary_sources` / `extra_sources`.

## Requirements

### Functional Requirements

- The `smart-search-cli` skill must describe `smart-search` as a reproducible
  evidence layer, not as a blanket replacement for native web search.
- The skill must describe, as **heuristic guidance** (not a numbered "must
  escalate when..." enumeration), when native semantic discovery is the right
  default. Illustrative examples — not an exhaustive trigger table — include
  lightweight exploration, query expansion, candidate source discovery,
  identifying likely official domains, aliases, version names, and search terms.
- The skill must describe, as **heuristic guidance**, when `smart-search`
  should be invoked along the **semantic-breadth axis**. Illustrative
  signals — not an exhaustive trigger table — include: native search
  results appear narrow, single-language, single-source, or biased;
  the query crosses languages or regions (e.g., Chinese / domestic /
  regional sources matter); the user wants neighboring/related sources
  from a known seed URL; the documentation site's structure matters;
  exploration would benefit from multi-provider coverage rather than a
  single backend's worldview.
- The skill must describe, as **heuristic guidance**, when `smart-search`
  should be invoked along the **evidence-depth axis**. Illustrative
  examples — not an exhaustive trigger table — include source-backed
  fact checking, current/high-risk claims, official/API/doc research,
  user-supplied URLs, multi-source comparisons, site mapping, and any
  task that asks for reproducible evidence.
- The skill must make clear that the two axes are independent: invoking
  the extension for semantic breadth does **not** automatically engage the
  audit hard constraint, and vice versa. The constraint applies when the
  AI uses smart-search results as the **evidence backing** for its
  answer.
- The skill body must be organized as three prose sections framed around
  *capability extension along two axes*, not workflow phases:
  1. **Baseline search (what native already does well)** — establish that the
     AI's native search/reasoning is the default and is sufficient for most
     casual lookup, while flagging baseline's two known limits: it can be
     **semantically narrow** (single backend / single language / single
     index), and it does not produce **auditable** evidence.
  2. **Where baseline isn't enough (heuristic signals on two axes)** —
     describe, as prose principles, both signal families:
     - **Semantic-breadth signals**: native results look narrow / biased /
       single-language / single-source; query needs neighbors of a seed
       URL; a documentation domain's structure matters; coverage across
       Chinese / regional / academic indices matters.
     - **Evidence-depth signals**: claim needs cited sources, official
       docs/API, current/high-risk data, user-supplied URLs,
       reproducibility, or audit.
  3. **`smart-search` as the dual-axis extension** — describe `smart-search`
     as the upgrade applied to baseline search along either or both axes,
     map providers/commands to their axis (Exa/Zhipu/Context7/`map`/
     `exa-similar` lean breadth; `fetch` + `primary_sources` lean depth),
     state the audit hard constraint **scoped to the evidence-depth axis**,
     and point to `references/cli-contract.md` for full command details.
  Concrete command examples remain available, but demoted to a "Command
  Reference" section or to `references/cli-contract.md`, so the skill body
  reads as a capability-extension explainer rather than a workflow guide or a
  feature catalog. The skill must not use phase-switching wording such as
  "first do X, then escalate to Y"; instead it should use upgrade wording
  such as "apply the extension when the answer's quality depends on broader
  semantic coverage or stronger evidence than baseline can provide".
- The skill must state that native search results are discovery hints, not final
  citations, when the task requires source-backed claims.
- The skill must preserve the existing evidence rules:
  - prefer JSON for agent parsing;
  - use `--output` for multi-source or citation-heavy work;
  - treat `extra_sources` as candidate sources until fetched or otherwise
    verified;
  - use `fetch` for exact pages that support final claims.
- Claude Code and Codex installs must receive the same workflow logic from the
  bundled skill assets.
- The setup and README messaging must not imply that Claude Code / Codex native
  web search should be disabled or deny-listed by default.
- The project must continue to avoid MCP compatibility as a requirement for this
  workflow.
- Existing provider routing rules and CLI command contracts must remain valid.

### Documentation Requirements

- README usage/setup text must explain the collaborative model:
  "native semantic discovery + Smart Search reproducible evidence".
- Setup wizard text must describe skill installation as teaching AI tools a
  collaborative evidence workflow, not forcing all searches through
  `smart-search`.
- `agents/openai.yaml` default prompt must reflect the same collaborative
  workflow for Codex/OpenAI-agent usage.
- Skill documentation and packaged skill assets must stay in sync.
- Any tests that currently enforce exclusive-native-search wording must be
  updated to enforce the new non-exclusive evidence workflow instead.

### Non-Goals

- Do not add an MCP server or GrokSearch-compatible MCP tools.
- Do not disable or deny-list Claude Code `WebSearch` / `WebFetch`.
- Do not make `smart-search` the mandatory path for trivial lookups that do not
  need evidence or reproducibility.
- Do not change provider APIs, API-key configuration semantics, or core search
  result schemas unless needed to document the workflow.
- Do not introduce per-client behavior divergence between Claude Code and Codex
  unless the platform requires a small installation-path difference.

## Acceptance Criteria

- [ ] `skills/smart-search-cli/SKILL.md` describes a two-stage workflow:
      native semantic discovery first when useful, then `smart-search` for
      reproducible evidence.
- [ ] `src/smart_search/assets/skills/smart-search-cli/SKILL.md` matches the
      source skill workflow.
- [ ] The skill no longer says agents must avoid native web search in the same
      task when `smart-search doctor` succeeds.
- [ ] The skill clearly says native search/discovery results must not be treated
      as final evidence for high-risk or citation-required claims.
- [ ] README setup/usage language presents skill injection as teaching AI tools
      when to use `smart-search`, not as forcing all web research through it.
- [ ] Setup wizard copy presents skill installation as a collaborative evidence
      workflow for AI tools.
- [ ] `skills/smart-search-cli/agents/openai.yaml` and the packaged copy use a
      default prompt aligned with native semantic discovery plus
      `smart-search` evidence hardening.
- [ ] Codex and Claude Code skill installation targets remain supported.
- [ ] Regression tests assert the new workflow contract and no longer require
      wording that says native web search is disabled.
- [ ] Regression tests assert the skill text describes the **dual-axis**
      extension explicitly, including at minimum anchors that name both
      axes: `semantic` (or `breadth`) AND `evidence` (or `audit`).
- [ ] Regression tests assert the skill text mentions at least one
      semantic-breadth signal (e.g., `narrow`, `single-language`,
      `multi-provider`, or `Chinese`) so the breadth axis cannot quietly
      disappear in future edits.
- [ ] Regression tests assert the skill text contains audit-trail anchor terms
      that cover the evidence hard constraint, including at minimum:
      `preserve`, `command line`, `primary_sources`, and `fetched`.
- [ ] Regression tests assert the skill text does **not** state or imply that
      `extra_sources` alone constitute audit evidence.
- [ ] Regression tests assert the skill text does **not** contain the old
      exclusive phrases: `native web search is disabled`,
      `Do not call ... native web search`, or
      `do not silently fall back to native web search`.
- [ ] Existing offline regression coverage passes.
- [ ] No MCP dependency or MCP entrypoint is added.

## Decisions

- This task includes skill docs, README/setup messaging, `agents/openai.yaml`,
  packaged skill assets, and tests.
- 2026-05-14 brainstorm calibration: the in-progress edit pass left four
  contract gaps that must be closed before completion. Tracked in
  `implement.md` under "Boundary Calibration":
  1. `tests/test_regression.py` must enforce that `extra_sources` is never
     paired with `evidence` / `proof` without a negation in skill text
     (PRD acceptance criterion at "Regression tests assert the skill text
     does not state or imply that `extra_sources` alone constitute audit
     evidence").
  2. `references/cli-contract.md` must contain a dedicated
     `## Local Wrapper Contract` section absorbing the Windows env-var,
     `config set` rerun, PATH-change, setup-wizard, Tavily Hikari, and
     Firecrawl REST base rules.
  3. `SKILL.md` must stay within the 70–90 line target by sinking the two
     generic security guardrails (API-key non-exposure, key rotation gate)
     into `cli-contract.md`'s Maintenance Guardrails.
  4. `tests/test_cli.py` setup-copy assertions must anchor on canonical
     names (`Smart Search Evidence Extension`, `Smart Search 扩展`),
     not on `Install the smart-search-cli skill`, so the test actually
     guards the new framing.
