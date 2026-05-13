from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PUBLIC_SKILL_DIR = ROOT / "skills" / "smart-search-cli"
PACKAGED_SKILL_DIR = ROOT / "src" / "smart_search" / "assets" / "skills" / "smart-search-cli"


def test_regression_does_not_create_repo_log_file():
    log_dir = ROOT / "logs"
    if not log_dir.exists():
        return
    assert not list(log_dir.glob("smart_search_*.log"))


def test_smart_search_skill_contract_enforces_cli_first():
    skill_dir = Path.home() / ".codex" / "skills" / "smart-search-cli"
    if not skill_dir.exists():
        return

    text = "\n".join(
        p.read_text(encoding="utf-8")
        for p in skill_dir.rglob("*")
        if p.is_file() and p.suffix in {".md", ".yaml", ".yml"}
    )

    forbidden_text = [
        "mcp__smart-search__",
        "get_sources",
        "get_config_info",
        "toggle_builtin_tools",
        "native web search fallback",
        "silently fallback",
    ]
    for phrase in forbidden_text:
        assert phrase not in text

    assert "native `web_search` is disabled" in text or "native web search is disabled" in text
    assert "do not silently fall back" in text


def _read_skill_tree(path: Path) -> str:
    return "\n".join(
        p.read_text(encoding="utf-8")
        for p in sorted(path.rglob("*"))
        if p.is_file() and p.suffix in {".md", ".yaml", ".yml"}
    )


def test_deep_research_skill_contract_public_and_packaged_assets_match():
    public_text = _read_skill_tree(PUBLIC_SKILL_DIR)
    packaged_text = _read_skill_tree(PACKAGED_SKILL_DIR)
    required_markers = [
        "Deep Research Mode",
        "深度搜索",
        "深度调研",
        "deep search",
        "deep research",
        "research_plan",
        "capability-based orchestration",
        "intent_signals",
        "capability_plan",
        "gap_check",
        "fetch_before_claim",
        "search`, `exa-search`, `exa-similar`, `zhipu-search`, `context7-library`, `context7-docs`, `fetch`, and `map`",
        "doctor` is preflight",
        "fixed topic recipe",
        "深度搜索一下最近的比特币行情",
        "C:\\tmp\\smart-search-evidence",
        "mock-full plus live-limited",
        "does not add or require a `smart-search deep` command",
        "does not change default `smart-search search`",
        "does not depend on an MCP session",
    ]
    for marker in required_markers:
        assert marker in public_text
        assert marker in packaged_text


def test_deep_research_cli_contract_documents_plan_and_smoke_matrix():
    public_contract = (PUBLIC_SKILL_DIR / "references" / "cli-contract.md").read_text(encoding="utf-8")
    packaged_contract = (PACKAGED_SKILL_DIR / "references" / "cli-contract.md").read_text(encoding="utf-8")
    required_markers = [
        "Deep Research Skill Contract",
        "not a new public CLI command",
        "must not change default `smart-search search` behavior",
        "`mode`: always `deep_research`",
        "`question`: the user's research question",
        "`difficulty`: `standard` or `high`",
        "`intent_signals`: dimensional signals",
        "`capability_plan`: the selected capability needs",
        "`evidence_policy`: default `fetch_before_claim`",
        "`steps`: ordered CLI command steps",
        "`gap_check`: how the agent verifies",
        "`final_answer_policy`: how to cite fetched evidence",
        "Allowed `tool` values are `search`, `exa-search`, `exa-similar`, `zhipu-search`, `context7-library`, `context7-docs`, `fetch`, and `map`",
        "`doctor` is a `preflight` action, not a `steps[]` item",
        "must not require fixed topic recipe ids",
        "fixed topic recipe ids are not required schema",
        "Mock-full coverage should cover trigger phrases",
        "Live-limited coverage should run `doctor`, one broad `search`, one `exa-search`, and one `fetch`",
        "rerun the affected smoke until it passes or is proven to be an external provider blocker",
    ]
    for marker in required_markers:
        assert marker in public_contract
        assert marker in packaged_contract


def test_deep_research_readme_documents_capability_orchestration():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    required_markers = [
        "Deep Research 不是固定题材配方",
        "`intent_signals`",
        "`capability_plan`",
        "`gap_check`",
        "`exa-similar`",
        "`context7-library`",
        "`doctor` 只是配置预检",
        "Deep Research is not a fixed topic recipe system",
        "not required schema enums",
        "`doctor` is preflight, not a research step",
        "Unsupported key claims must be fetched or downgraded to unverified candidates",
    ]
    for marker in required_markers:
        assert marker in readme


def test_deep_research_shared_skill_files_are_synchronized():
    shared_files = [
        "SKILL.md",
        "references/cli-contract.md",
    ]
    for relative in shared_files:
        assert (PUBLIC_SKILL_DIR / relative).read_text(encoding="utf-8") == (
            PACKAGED_SKILL_DIR / relative
        ).read_text(encoding="utf-8")
