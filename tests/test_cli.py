import json
import asyncio
from smart_search import cli


def test_help_contains_commands(capsys):
    try:
        cli.main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0

    out = capsys.readouterr().out
    assert "search" in out
    assert "doctor" in out
    assert "regression" in out


def test_each_subcommand_help_exits_successfully(capsys):
    commands = [
        ["search", "--help"],
        ["fetch", "--help"],
        ["map", "--help"],
        ["exa-search", "--help"],
        ["exa-similar", "--help"],
        ["doctor", "--help"],
        ["model", "--help"],
        ["model", "set", "--help"],
        ["model", "current", "--help"],
        ["regression", "--help"],
    ]

    for command in commands:
        try:
            cli.main(command)
        except SystemExit as exc:
            assert exc.code == 0

    out = capsys.readouterr().out
    assert "usage: smart-search search" in out
    assert "usage: smart-search regression" in out


def test_search_help_exposes_timeout(capsys):
    try:
        cli.main(["search", "--help"])
    except SystemExit as exc:
        assert exc.code == 0

    out = capsys.readouterr().out
    assert "--timeout SECONDS" in out


def test_search_outputs_json_and_file(monkeypatch, capsys):
    async def fake_search(query, platform="", model="", extra_sources=0):
        return {
            "ok": True,
            "query": query,
            "content": "Answer",
            "sources": [{"url": "https://example.com", "title": "Example"}],
            "sources_count": 1,
        }

    monkeypatch.setattr(cli.service, "search", fake_search)
    written = {}

    def fake_write_output(path, content):
        written["path"] = path
        written["content"] = content

    monkeypatch.setattr(cli.service, "write_output", fake_write_output)
    output = "C:/tmp/smart-search-cli-test-result.json"

    code = cli.main(["search", "query", "--output", output])

    assert code == cli.EXIT_OK
    stdout_data = json.loads(capsys.readouterr().out)
    file_data = json.loads(written["content"])
    assert written["path"] == output
    assert stdout_data["sources_count"] == 1
    assert file_data["content"] == "Answer"


def test_search_timeout_outputs_json_and_exit_4(monkeypatch, capsys):
    async def slow_search(query, platform="", model="", extra_sources=0):
        await asyncio.sleep(1)
        return {
            "ok": True,
            "query": query,
            "content": "late answer",
            "sources": [{"url": "https://example.com"}],
            "sources_count": 1,
        }

    monkeypatch.setattr(cli.service, "search", slow_search)

    code = cli.main(["search", "slow query", "--timeout", "0.01", "--format", "markdown"])

    assert code == cli.EXIT_NETWORK_ERROR
    out = capsys.readouterr()
    data = json.loads(out.out)
    assert out.err == ""
    assert data["ok"] is False
    assert data["error_type"] == "network_error"
    assert "0.01" in data["error"]
    assert "seconds" in data["error"]
    assert data["query"] == "slow query"
    assert data["content"] == ""
    assert data["sources"] == []
    assert data["sources_count"] == 0


def test_markdown_search_includes_sources(monkeypatch, capsys):
    async def fake_search(query, platform="", model="", extra_sources=0):
        return {
            "ok": True,
            "content": "Answer",
            "sources": [{"url": "https://example.com", "title": "Example"}],
            "sources_count": 1,
        }

    monkeypatch.setattr(cli.service, "search", fake_search)

    code = cli.main(["search", "query", "--format", "markdown"])

    assert code == cli.EXIT_OK
    out = capsys.readouterr().out
    assert "Answer" in out
    assert "[Example](https://example.com)" in out


def test_config_error_exit_code(monkeypatch, capsys):
    async def fake_doctor():
        return {"ok": False, "error_type": "config_error", "SMART_SEARCH_API_KEY": "未配置"}

    monkeypatch.setattr(cli.service, "doctor", fake_doctor)

    code = cli.main(["doctor"])

    assert code == cli.EXIT_CONFIG_ERROR
    assert json.loads(capsys.readouterr().out)["SMART_SEARCH_API_KEY"] == "未配置"


def test_network_error_exit_code(monkeypatch, capsys):
    async def fake_fetch(url):
        return {"ok": False, "error_type": "network_error", "error": "upstream timeout", "url": url}

    monkeypatch.setattr(cli.service, "fetch", fake_fetch)

    code = cli.main(["fetch", "https://example.com"])

    assert code == cli.EXIT_NETWORK_ERROR
    assert json.loads(capsys.readouterr().out)["error"] == "upstream timeout"


def test_real_doctor_missing_primary_url_returns_config_exit(monkeypatch, capsys):
    secret = "placeholder-test-secret"
    monkeypatch.delenv("SMART_SEARCH_API_URL", raising=False)
    monkeypatch.setenv("SMART_SEARCH_API_KEY", secret)
    monkeypatch.delenv("EXA_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)

    code = cli.main(["doctor"])

    out = capsys.readouterr().out
    data = json.loads(out)
    assert code == cli.EXIT_CONFIG_ERROR
    assert data["ok"] is False
    assert data["error_type"] == "config_error"
    assert secret not in out


def test_model_set_uses_service(monkeypatch, capsys):
    def fake_set_model(model):
        return {"ok": True, "previous_model": "old", "current_model": model, "config_file": "C:/tmp/smart-search-config.json"}

    monkeypatch.setattr(cli.service, "set_model", fake_set_model)

    code = cli.main(["model", "set", "grok-4-fast"])

    assert code == cli.EXIT_OK
    assert json.loads(capsys.readouterr().out)["current_model"] == "grok-4-fast"


def test_regression_invokes_pytest(monkeypatch):
    captured = {}

    def fake_call(cmd, cwd):
        captured["cmd"] = cmd
        captured["cwd"] = cwd
        return 0

    monkeypatch.setattr(cli.subprocess, "call", fake_call)

    code = cli.main(["regression"])

    assert code == 0
    assert "-m" in captured["cmd"]
    assert "pytest" in captured["cmd"]
    assert "tests/test_cli.py" in captured["cmd"]
