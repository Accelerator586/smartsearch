from pathlib import Path


def test_regression_does_not_create_repo_log_file():
    log_dir = Path(__file__).resolve().parent.parent / "logs"
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
        "web_fetch",
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
