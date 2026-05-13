import json

import httpx
import pytest

from smart_search import service


def _reset_config(monkeypatch, tmp_path):
    fake_config_file = tmp_path / "config.json"
    monkeypatch.setattr(service.config, "_config_file", fake_config_file)
    monkeypatch.setattr(service.config, "_cached_model", None)
    for key in [
        "SMART_SEARCH_API_URL",
        "SMART_SEARCH_API_KEY",
        "SMART_SEARCH_API_MODE",
        "SMART_SEARCH_XAI_TOOLS",
        "SMART_SEARCH_MODEL",
        "XAI_API_URL",
        "XAI_API_KEY",
        "XAI_MODEL",
        "XAI_TOOLS",
        "OPENAI_COMPATIBLE_API_URL",
        "OPENAI_COMPATIBLE_API_KEY",
        "OPENAI_COMPATIBLE_MODEL",
        "EXA_API_KEY",
        "EXA_BASE_URL",
        "TAVILY_API_KEY",
        "TAVILY_API_URL",
        "FIRECRAWL_API_KEY",
        "FIRECRAWL_API_URL",
    ]:
        monkeypatch.delenv(key, raising=False)
    return fake_config_file


def test_model_set_and_current_use_temp_config(monkeypatch):
    fake_config_file = service.Path("memory:/smart-search-test-config.json")
    stored_config = {}

    def fake_load_config_file():
        return stored_config.copy()

    def fake_save_config_file(config_data):
        stored_config.clear()
        stored_config.update(config_data)

    monkeypatch.setattr(service.config, "_config_file", fake_config_file)
    monkeypatch.setattr(service.config, "_cached_model", None)
    monkeypatch.setattr(service.config, "_load_config_file", fake_load_config_file)
    monkeypatch.setattr(service.config, "_save_config_file", fake_save_config_file)
    monkeypatch.delenv("SMART_SEARCH_MODEL", raising=False)

    set_result = service.set_model("grok-4-fast")
    current_result = service.current_model()

    assert set_result["ok"] is True
    assert set_result["current_model"] == "grok-4-fast"
    assert current_result["model"] == "grok-4-fast"
    assert stored_config["SMART_SEARCH_MODEL"] == "grok-4-fast"
    assert set_result["config_file"] == str(fake_config_file)


def test_config_set_list_unset_and_path(monkeypatch, tmp_path):
    fake_config_file = _reset_config(monkeypatch, tmp_path)

    set_result = service.config_set("SMART_SEARCH_API_KEY", "sk-test-secret")
    list_result = service.config_list()
    path_result = service.config_path()

    assert set_result["ok"] is True
    assert set_result["value"].startswith("sk-t")
    assert "secret" not in json.dumps(list_result)
    assert list_result["values"]["SMART_SEARCH_API_KEY"].startswith("sk-t")
    assert path_result["config_file"] == str(fake_config_file)

    unset_result = service.config_unset("SMART_SEARCH_API_KEY")
    assert unset_result["ok"] is True
    assert "SMART_SEARCH_API_KEY" not in service.config_list()["values"]


def test_config_file_supplies_primary_settings(monkeypatch, tmp_path):
    _reset_config(monkeypatch, tmp_path)

    service.config_set("SMART_SEARCH_API_URL", "https://config.example.com/v1")
    service.config_set("SMART_SEARCH_API_KEY", "sk-config-secret")
    service.config_set("SMART_SEARCH_MODEL", "config-model")

    assert service.config.smart_search_api_url == "https://config.example.com/v1"
    assert service.config.smart_search_api_key == "sk-config-secret"
    assert service.config.smart_search_model == "config-model"


def test_environment_overrides_config_file(monkeypatch, tmp_path):
    _reset_config(monkeypatch, tmp_path)

    service.config_set("SMART_SEARCH_API_URL", "https://config.example.com/v1")
    monkeypatch.setenv("SMART_SEARCH_API_URL", "https://env.example.com/v1")

    assert service.config.smart_search_api_url == "https://env.example.com/v1"
    assert service.config.get_config_source("SMART_SEARCH_API_URL") == "environment"
    assert service.config.get_config_source("SMART_SEARCH_API_KEY") == "default"


def test_config_sources_report_config_file(monkeypatch, tmp_path):
    _reset_config(monkeypatch, tmp_path)

    service.config_set("SMART_SEARCH_API_KEY", "sk-config-secret")

    sources = service.config.get_config_sources()

    assert sources["SMART_SEARCH_API_KEY"] == "config_file"
    assert sources["SMART_SEARCH_API_URL"] == "default"


def test_primary_api_mode_auto_resolves_xai(monkeypatch, tmp_path):
    _reset_config(monkeypatch, tmp_path)

    assert service.config.resolve_primary_api_mode("https://api.x.ai/v1") == "xai-responses"
    assert service.config.resolve_primary_api_mode("https://api.example.com/v1") == "chat-completions"


def test_primary_api_mode_can_be_configured(monkeypatch, tmp_path):
    _reset_config(monkeypatch, tmp_path)

    service.config_set("SMART_SEARCH_API_MODE", "chat-completions")

    assert service.config.resolve_primary_api_mode("https://api.x.ai/v1") == "chat-completions"
    assert service.config.get_config_sources()["SMART_SEARCH_API_MODE"] == "config_file"


def test_xai_tools_validation(monkeypatch, tmp_path):
    _reset_config(monkeypatch, tmp_path)

    service.config_set("SMART_SEARCH_XAI_TOOLS", "web_search,x_search,web_search")
    assert service.config.parse_xai_tools() == ["web_search", "x_search"]

    service.config_set("SMART_SEARCH_XAI_TOOLS", "web_search,bad_tool")
    with pytest.raises(ValueError, match="Invalid SMART_SEARCH_XAI_TOOLS"):
        service.config.parse_xai_tools()


@pytest.mark.asyncio
async def test_search_returns_sources(monkeypatch):
    monkeypatch.setenv("SMART_SEARCH_API_URL", "https://api.example.com/v1")
    monkeypatch.setenv("SMART_SEARCH_API_KEY", "sk-test-secret")

    async def fake_search(self, query, platform="", ctx=None):
        return 'Answer.\n\nsources([{"url":"https://example.com","title":"Example"}])'

    monkeypatch.setattr(service.OpenAICompatibleSearchProvider, "search", fake_search)
    monkeypatch.setattr(service, "call_tavily_search", lambda *a, **k: None)
    monkeypatch.setattr(service, "call_firecrawl_search", lambda *a, **k: None)

    result = await service.search("what is example")

    assert result["ok"] is True
    assert result["primary_api_mode"] == "chat-completions"
    assert result["content"] == "Answer."
    assert result["sources_count"] == 1
    assert result["primary_sources_count"] == 1
    assert result["extra_sources_count"] == 0
    assert result["sources"][0]["url"] == "https://example.com"
    assert result["primary_sources"][0]["url"] == "https://example.com"
    assert result["extra_sources"] == []
    assert result["source_warning"] == ""


@pytest.mark.asyncio
async def test_search_splits_primary_and_extra_sources(monkeypatch):
    monkeypatch.setenv("SMART_SEARCH_API_URL", "https://api.example.com/v1")
    monkeypatch.setenv("SMART_SEARCH_API_KEY", "sk-test-secret")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-secret")

    async def fake_search(self, query, platform="", ctx=None):
        return 'Answer.\n\nsources([{"url":"https://primary.example.com","title":"Primary"}])'

    async def fake_tavily_search(query, max_results=6):
        return [{"url": "https://extra.example.com", "title": "Extra", "content": "candidate"}]

    monkeypatch.setattr(service.OpenAICompatibleSearchProvider, "search", fake_search)
    monkeypatch.setattr(service, "call_tavily_search", fake_tavily_search)
    monkeypatch.setattr(service, "call_firecrawl_search", lambda *a, **k: None)

    result = await service.search("what is example", extra_sources=1)

    assert result["ok"] is True
    assert result["sources_count"] == 2
    assert result["primary_sources_count"] == 1
    assert result["extra_sources_count"] == 1
    assert result["primary_sources"][0]["url"] == "https://primary.example.com"
    assert result["extra_sources"][0]["url"] == "https://extra.example.com"
    assert result["extra_sources"][0]["provider"] == "tavily"
    assert "not automatically used to verify generated content" in result["source_warning"]


@pytest.mark.asyncio
async def test_search_uses_xai_responses_for_api_x_ai(monkeypatch):
    monkeypatch.setenv("SMART_SEARCH_API_URL", "https://api.x.ai/v1")
    monkeypatch.setenv("SMART_SEARCH_API_KEY", "sk-test-secret")
    captured = {}

    async def fake_search(self, query, platform="", ctx=None):
        captured["provider"] = self.__class__.__name__
        captured["tools"] = self.tools
        return "Answer [[1]](https://example.com)."

    monkeypatch.setattr(service.XAIResponsesSearchProvider, "search", fake_search)
    monkeypatch.setattr(service, "call_tavily_search", lambda *a, **k: None)
    monkeypatch.setattr(service, "call_firecrawl_search", lambda *a, **k: None)

    result = await service.search("what is example")

    assert result["ok"] is True
    assert result["primary_api_mode"] == "xai-responses"
    assert captured["provider"] == "XAIResponsesSearchProvider"
    assert captured["tools"] == ["web_search", "x_search"]
    assert result["sources"][0]["url"] == "https://example.com"


@pytest.mark.asyncio
async def test_search_fallbacks_from_xai_responses_to_openai_compatible(monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "xai-test-secret")
    monkeypatch.setenv("XAI_MODEL", "xai-model")
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_URL", "https://relay.example.com/v1")
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_KEY", "relay-test-secret")
    monkeypatch.setenv("OPENAI_COMPATIBLE_MODEL", "relay-model")
    captured = []

    async def failing_xai(self, query, platform="", ctx=None):
        captured.append((self.__class__.__name__, self.api_url, self.api_key, self.model))
        request = httpx.Request("POST", "https://api.x.ai/v1/responses")
        response = httpx.Response(503, text="responses unavailable", request=request)
        raise httpx.HTTPStatusError("responses unavailable", request=request, response=response)

    async def fallback_openai(self, query, platform="", ctx=None):
        captured.append((self.__class__.__name__, self.api_url, self.api_key, self.model))
        return 'Fallback answer.\n\nsources([{"url":"https://fallback.example.com","title":"Fallback"}])'

    monkeypatch.setattr(service.XAIResponsesSearchProvider, "search", failing_xai)
    monkeypatch.setattr(service.OpenAICompatibleSearchProvider, "search", fallback_openai)

    result = await service.search("what is example")

    assert result["ok"] is True
    assert result["content"] == "Fallback answer."
    assert result["fallback_used"] is True
    assert [a["provider"] for a in result["provider_attempts"][:2]] == ["xAI Responses", "OpenAI-compatible"]
    assert result["provider_attempts"][0]["status"] == "error"
    assert result["provider_attempts"][1]["status"] == "ok"
    assert result["primary_api_mode"] == "chat-completions"
    assert result["model"] == "relay-model"
    assert result["routing_decision"]["main_search_chain"] == ["xai-responses", "openai-compatible"]
    assert captured == [
        ("XAIResponsesSearchProvider", "https://api.x.ai/v1", "xai-test-secret", "xai-model"),
        ("OpenAICompatibleSearchProvider", "https://relay.example.com/v1", "relay-test-secret", "relay-model"),
    ]


@pytest.mark.asyncio
async def test_search_does_not_fake_openai_compatible_fallback_when_only_xai_configured(monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "xai-test-secret")

    async def failing_xai(self, query, platform="", ctx=None):
        request = httpx.Request("POST", "https://api.x.ai/v1/responses")
        response = httpx.Response(503, text="responses unavailable", request=request)
        raise httpx.HTTPStatusError("responses unavailable", request=request, response=response)

    async def should_not_run(self, query, platform="", ctx=None):
        raise AssertionError("OpenAI-compatible fallback requires its own configured URL and key")

    monkeypatch.setattr(service.XAIResponsesSearchProvider, "search", failing_xai)
    monkeypatch.setattr(service.OpenAICompatibleSearchProvider, "search", should_not_run)

    result = await service.search("what is example")

    assert result["ok"] is False
    assert result["fallback_used"] is False
    assert [a["provider"] for a in result["provider_attempts"]] == ["xAI Responses"]


@pytest.mark.asyncio
async def test_search_accepts_only_openai_compatible_as_main_provider(monkeypatch):
    monkeypatch.setenv("SMART_SEARCH_MINIMUM_PROFILE", "standard")
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_URL", "https://relay.example.com/v1")
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_KEY", "relay-test-secret")
    monkeypatch.setenv("EXA_API_KEY", "exa-test-secret")
    monkeypatch.setenv("TAVILY_API_KEY", "tavily-test-secret")

    async def fake_search(self, query, platform="", ctx=None):
        return "Relay answer."

    monkeypatch.setattr(service.OpenAICompatibleSearchProvider, "search", fake_search)

    result = await service.search("what is example")

    assert result["ok"] is True
    assert result["primary_api_mode"] == "chat-completions"
    assert result["routing_decision"]["main_search_chain"] == ["openai-compatible"]
    assert result["capability_status"]["main_search"]["configured"] == ["openai-compatible"]


@pytest.mark.asyncio
async def test_search_provider_filter_can_select_openai_compatible(monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "xai-test-secret")
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_URL", "https://relay.example.com/v1")
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_KEY", "relay-test-secret")

    async def should_not_run(self, query, platform="", ctx=None):
        raise AssertionError("xAI should be filtered out")

    async def fallback_openai(self, query, platform="", ctx=None):
        return "Relay answer."

    monkeypatch.setattr(service.XAIResponsesSearchProvider, "search", should_not_run)
    monkeypatch.setattr(service.OpenAICompatibleSearchProvider, "search", fallback_openai)

    result = await service.search("what is example", providers="openai-compatible")

    assert result["ok"] is True
    assert result["routing_decision"]["main_search_chain"] == ["openai-compatible"]
    assert [a["provider"] for a in result["provider_attempts"]] == ["OpenAI-compatible"]


@pytest.mark.asyncio
@pytest.mark.parametrize("query", ["nba战报", "NBA比分", "今日赛程"])
async def test_balanced_current_sports_queries_use_web_search_reinforcement(monkeypatch, query):
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_URL", "https://relay.example.com/v1")
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_KEY", "relay-test-secret")
    monkeypatch.setenv("EXA_API_KEY", "exa-test-secret")
    monkeypatch.setenv("TAVILY_API_KEY", "tavily-test-secret")

    async def fake_search(self, query, platform="", ctx=None):
        return "Sports answer."

    async def fake_tavily_search(query, max_results=6):
        return [{"url": "https://sports.example.com", "title": "Sports", "content": "score"}]

    monkeypatch.setattr(service.OpenAICompatibleSearchProvider, "search", fake_search)
    monkeypatch.setattr(service, "call_tavily_search", fake_tavily_search)

    result = await service.search(query, validation="balanced")

    assert result["ok"] is True
    assert result["routing_decision"]["zh_current_intent"] is True
    assert result["routing_decision"]["web_current_intent"] is True
    assert "web_search" in result["routing_decision"]["supplemental_paths"]
    assert any(attempt["capability"] == "web_search" and attempt["status"] == "ok" for attempt in result["provider_attempts"])
    assert result["extra_sources"][0]["url"] == "https://sports.example.com"


@pytest.mark.asyncio
async def test_chinese_language_request_does_not_trigger_current_web_search(monkeypatch):
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_URL", "https://relay.example.com/v1")
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_KEY", "relay-test-secret")
    monkeypatch.setenv("EXA_API_KEY", "exa-test-secret")
    monkeypatch.setenv("TAVILY_API_KEY", "tavily-test-secret")

    async def fake_search(self, query, platform="", ctx=None):
        return "Language answer."

    async def should_not_run_web_search(query, count=5, providers="auto", fallback="auto"):
        raise AssertionError("generic Chinese-language requests should not trigger current web_search")

    monkeypatch.setattr(service.OpenAICompatibleSearchProvider, "search", fake_search)
    monkeypatch.setattr(service, "_run_web_search_fallback", should_not_run_web_search)

    result = await service.search("中文解释 Python 函数", validation="balanced")

    assert result["ok"] is True
    assert result["routing_decision"]["web_current_intent"] is False
    assert "web_search" not in result["routing_decision"]["supplemental_paths"]
    assert all(attempt["capability"] != "web_search" for attempt in result["provider_attempts"])


@pytest.mark.asyncio
async def test_docs_query_routes_docs_without_current_web_search(monkeypatch):
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_URL", "https://relay.example.com/v1")
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_KEY", "relay-test-secret")
    monkeypatch.setenv("EXA_API_KEY", "exa-test-secret")
    monkeypatch.setenv("TAVILY_API_KEY", "tavily-test-secret")

    async def fake_search(self, query, platform="", ctx=None):
        return "Docs answer."

    async def fake_docs_search(query, providers="auto", fallback="auto"):
        return [{"url": "https://docs.example.com", "provider": "exa"}], [
            {"capability": "docs_search", "provider": "exa", "status": "ok", "elapsed_ms": 1, "result_count": 1}
        ]

    async def should_not_run_web_search(query, count=5, providers="auto", fallback="auto"):
        raise AssertionError("docs query should not trigger current web_search")

    monkeypatch.setattr(service.OpenAICompatibleSearchProvider, "search", fake_search)
    monkeypatch.setattr(service, "_run_docs_search_fallback", fake_docs_search)
    monkeypatch.setattr(service, "_run_web_search_fallback", should_not_run_web_search)

    result = await service.search("React useEffect API docs 中文解释", validation="balanced")

    assert result["ok"] is True
    assert result["routing_decision"]["docs_intent"] is True
    assert result["routing_decision"]["web_current_intent"] is False
    assert result["routing_decision"]["supplemental_paths"] == ["docs_search"]
    assert any(attempt["capability"] == "docs_search" for attempt in result["provider_attempts"])
    assert all(attempt["capability"] != "web_search" for attempt in result["provider_attempts"])


@pytest.mark.asyncio
async def test_strict_still_uses_web_search_without_current_keyword(monkeypatch):
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_URL", "https://relay.example.com/v1")
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_KEY", "relay-test-secret")
    monkeypatch.setenv("EXA_API_KEY", "exa-test-secret")
    monkeypatch.setenv("TAVILY_API_KEY", "tavily-test-secret")

    async def fake_search(self, query, platform="", ctx=None):
        return "Strict answer."

    async def fake_tavily_search(query, max_results=6):
        return [{"url": "https://strict.example.com", "title": "Strict", "content": "evidence"}]

    monkeypatch.setattr(service.OpenAICompatibleSearchProvider, "search", fake_search)
    monkeypatch.setattr(service, "call_tavily_search", fake_tavily_search)

    result = await service.search("plain evergreen query", validation="strict")

    assert result["ok"] is True
    assert result["routing_decision"]["web_current_intent"] is False
    assert "web_search" in result["routing_decision"]["supplemental_paths"]
    assert any(attempt["capability"] == "web_search" and attempt["status"] == "ok" for attempt in result["provider_attempts"])


@pytest.mark.asyncio
async def test_search_respects_fallback_off_for_main_search(monkeypatch):
    monkeypatch.setenv("SMART_SEARCH_API_URL", "https://api.x.ai/v1")
    monkeypatch.setenv("SMART_SEARCH_API_KEY", "sk-test-secret")

    async def failing_xai(self, query, platform="", ctx=None):
        request = httpx.Request("POST", "https://api.x.ai/v1/responses")
        response = httpx.Response(503, text="responses unavailable", request=request)
        raise httpx.HTTPStatusError("responses unavailable", request=request, response=response)

    async def should_not_run(self, query, platform="", ctx=None):
        raise AssertionError("OpenAI-compatible fallback should not run when fallback is off")

    monkeypatch.setattr(service.XAIResponsesSearchProvider, "search", failing_xai)
    monkeypatch.setattr(service.OpenAICompatibleSearchProvider, "search", should_not_run)

    result = await service.search("what is example", fallback="off")

    assert result["ok"] is False
    assert result["fallback_used"] is False
    assert [a["provider"] for a in result["provider_attempts"]] == ["xAI Responses"]


@pytest.mark.asyncio
async def test_search_reports_invalid_xai_tools_as_parameter_error(monkeypatch):
    monkeypatch.setenv("SMART_SEARCH_API_URL", "https://api.x.ai/v1")
    monkeypatch.setenv("SMART_SEARCH_API_KEY", "sk-test-secret")
    monkeypatch.setenv("SMART_SEARCH_XAI_TOOLS", "web_search,code_interpreter")

    result = await service.search("what is example")

    assert result["ok"] is False
    assert result["error_type"] == "parameter_error"
    assert "Invalid SMART_SEARCH_XAI_TOOLS" in result["error"]
    assert result["primary_sources"] == []
    assert result["extra_sources"] == []


@pytest.mark.asyncio
async def test_search_reports_primary_provider_http_error(monkeypatch):
    monkeypatch.setenv("SMART_SEARCH_API_URL", "https://api.x.ai/v1")
    monkeypatch.setenv("SMART_SEARCH_API_KEY", "sk-test-secret")

    async def failing_search(self, query, platform="", ctx=None):
        request = httpx.Request("POST", "https://api.x.ai/v1/responses")
        response = httpx.Response(422, text="bad tools", request=request)
        raise httpx.HTTPStatusError("bad response", request=request, response=response)

    async def should_not_hide_failure(*args, **kwargs):
        return [{"url": "https://extra.example.com"}]

    monkeypatch.setattr(service.XAIResponsesSearchProvider, "search", failing_search)
    monkeypatch.setattr(service, "call_tavily_search", should_not_hide_failure)

    result = await service.search("what is example", extra_sources=1, fallback="off")

    assert result["ok"] is False
    assert result["error_type"] == "network_error"
    assert result["primary_api_mode"] == "xai-responses"
    assert "xAI Responses HTTP 422" in result["error"]
    assert "bad tools" in result["error"]
    assert result["sources"] == []
    assert result["primary_sources"] == []
    assert result["extra_sources"] == []


@pytest.mark.asyncio
async def test_fetch_prefers_tavily(monkeypatch):
    async def yes_tavily(url):
        return "# Tavily Page"

    async def no_firecrawl(url, ctx=None):
        raise AssertionError("Firecrawl should not run when Tavily succeeds")

    monkeypatch.setattr(service, "call_tavily_extract", yes_tavily)
    monkeypatch.setattr(service, "call_firecrawl_scrape", no_firecrawl)

    result = await service.fetch("https://example.com")

    assert result["ok"] is True
    assert result["provider"] == "tavily"
    assert result["content"] == "# Tavily Page"


@pytest.mark.asyncio
async def test_fetch_fallbacks_to_firecrawl(monkeypatch):
    async def no_tavily(url):
        return None

    async def yes_firecrawl(url, ctx=None):
        return "# Page"

    monkeypatch.setattr(service, "call_tavily_extract", no_tavily)
    monkeypatch.setattr(service, "call_firecrawl_scrape", yes_firecrawl)

    result = await service.fetch("https://example.com")

    assert result["ok"] is True
    assert result["provider"] == "firecrawl"
    assert result["content"] == "# Page"


@pytest.mark.asyncio
async def test_fetch_reports_config_error_without_extract_keys(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)

    async def no_tavily(url):
        return None

    async def no_firecrawl(url, ctx=None):
        return None

    monkeypatch.setattr(service, "call_tavily_extract", no_tavily)
    monkeypatch.setattr(service, "call_firecrawl_scrape", no_firecrawl)

    result = await service.fetch("https://example.com")

    assert result["ok"] is False
    assert result["error_type"] == "config_error"


@pytest.mark.asyncio
async def test_fetch_reports_network_error_when_providers_fail(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "tavily-secret")
    monkeypatch.setenv("FIRECRAWL_API_KEY", "firecrawl-secret")

    async def no_tavily(url):
        return None

    async def no_firecrawl(url, ctx=None):
        return None

    monkeypatch.setattr(service, "call_tavily_extract", no_tavily)
    monkeypatch.setattr(service, "call_firecrawl_scrape", no_firecrawl)

    result = await service.fetch("https://example.com")

    assert result["ok"] is False
    assert result["error_type"] == "network_error"


@pytest.mark.asyncio
async def test_tavily_custom_base_is_used_for_search_extract_and_map(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "tavily-test-secret")
    monkeypatch.setenv("TAVILY_API_URL", "https://tavily.example.com/api/tavily")
    calls = []

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, headers, json):
            calls.append((url, json))
            if url.endswith("/search"):
                payload = {"results": [{"title": "Search", "url": "https://example.com", "content": "body", "score": 0.9}]}
            elif url.endswith("/extract"):
                payload = {"results": [{"raw_content": "# Extracted"}], "failed_results": []}
            elif url.endswith("/map"):
                payload = {"base_url": json["url"], "results": ["https://example.com/docs"], "response_time": 0.1}
            else:
                payload = {}
            return httpx.Response(200, json=payload, request=httpx.Request("POST", url))

    monkeypatch.setattr(service.httpx, "AsyncClient", FakeAsyncClient)

    search_result = await service.call_tavily_search("query", max_results=1)
    extract_result = await service.call_tavily_extract("https://example.com")
    map_result = await service.call_tavily_map("https://example.com", timeout=1)

    assert [call[0] for call in calls] == [
        "https://tavily.example.com/api/tavily/search",
        "https://tavily.example.com/api/tavily/extract",
        "https://tavily.example.com/api/tavily/map",
    ]
    assert search_result[0]["url"] == "https://example.com"
    assert extract_result == "# Extracted"
    assert map_result["ok"] is True
    assert map_result["results"] == ["https://example.com/docs"]


@pytest.mark.asyncio
async def test_firecrawl_custom_base_is_used_for_search_and_scrape(monkeypatch):
    monkeypatch.setenv("FIRECRAWL_API_KEY", "firecrawl-test-secret")
    monkeypatch.setenv("FIRECRAWL_API_URL", "https://firecrawl.example.com/v2")
    calls = []

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, headers, json):
            calls.append((url, json))
            if url.endswith("/search"):
                payload = {"data": {"web": [{"title": "Result", "url": "https://example.com", "description": "desc"}]}}
            elif url.endswith("/scrape"):
                payload = {"data": {"markdown": "# Scraped"}}
            else:
                payload = {}
            return httpx.Response(200, json=payload, request=httpx.Request("POST", url))

    monkeypatch.setattr(service.httpx, "AsyncClient", FakeAsyncClient)

    search_result = await service.call_firecrawl_search("query", limit=1)
    scrape_result = await service.call_firecrawl_scrape("https://example.com")

    assert [call[0] for call in calls] == [
        "https://firecrawl.example.com/v2/search",
        "https://firecrawl.example.com/v2/scrape",
    ]
    assert search_result[0]["url"] == "https://example.com"
    assert scrape_result == "# Scraped"


@pytest.mark.asyncio
async def test_exa_search_passes_parameters(monkeypatch):
    monkeypatch.setenv("EXA_API_KEY", "exa-secret")
    captured = {}

    async def fake_search(self, **kwargs):
        captured.update(kwargs)
        return json.dumps({"ok": True, "results": [], "total": 0})

    monkeypatch.setattr(service.ExaSearchProvider, "search", fake_search)

    result = await service.exa_search(
        "python docs",
        num_results=2,
        include_text=True,
        include_domains="docs.python.org,developer.mozilla.org",
    )

    assert result["ok"] is True
    assert captured["num_results"] == 2
    assert captured["include_text"] is True
    assert captured["include_domains"] == ["docs.python.org", "developer.mozilla.org"]


@pytest.mark.asyncio
async def test_exa_search_normalizes_error_json(monkeypatch):
    monkeypatch.setenv("EXA_API_KEY", "exa-secret")

    async def fake_search(self, **kwargs):
        return json.dumps({"ok": False, "error": "exa failed"})

    monkeypatch.setattr(service.ExaSearchProvider, "search", fake_search)

    result = await service.exa_search("python docs")

    assert result["ok"] is False
    assert result["error_type"] == "network_error"
    assert result["error"] == "exa failed"


@pytest.mark.asyncio
async def test_doctor_redacts_secret_and_reports_config_error(monkeypatch):
    monkeypatch.setenv("SMART_SEARCH_API_KEY", "placeholder-test-secret")
    monkeypatch.delenv("SMART_SEARCH_API_URL", raising=False)

    result = await service.doctor()
    dumped = json.dumps(result, ensure_ascii=False)

    assert "placeholder-test-secret" not in dumped
    assert "❌" not in dumped
    assert "✅" not in dumped
    assert result["ok"] is False
    assert result["error_type"] == "config_error"
    assert result["primary_connection_test"]["status"] == "config_error"


@pytest.mark.asyncio
async def test_doctor_reports_invalid_validation_config(monkeypatch):
    monkeypatch.setenv("SMART_SEARCH_API_URL", "https://api.example.com/v1")
    monkeypatch.setenv("SMART_SEARCH_API_KEY", "sk-test-secret")
    monkeypatch.setenv("SMART_SEARCH_VALIDATION_LEVEL", "banana")

    result = await service.doctor()

    assert result["ok"] is False
    assert result["error_type"] == "parameter_error"
    assert "Invalid SMART_SEARCH_VALIDATION_LEVEL" in result["error"]
    assert result["SMART_SEARCH_VALIDATION_LEVEL"] == "banana"


@pytest.mark.asyncio
async def test_primary_connection_falls_back_to_chat_when_models_endpoint_fails(monkeypatch):
    calls = []

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url, headers):
            calls.append(("get", url))
            return httpx.Response(
                401,
                json={"error": {"message": "models blocked"}},
                request=httpx.Request("GET", url),
            )

        async def post(self, url, headers, json):
            calls.append(("post", url, json["model"]))
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "ok"}}]},
                request=httpx.Request("POST", url),
            )

    monkeypatch.setattr(service.httpx, "AsyncClient", FakeAsyncClient)

    result = await service._test_primary_connection("https://api.example.com/v1", "sk-test-secret", "grok-4.3")

    assert result["status"] == "ok"
    assert result["models_endpoint_test"]["status"] == "warning"
    assert result["chat_completion_test"]["status"] == "ok"
    assert calls[0] == ("get", "https://api.example.com/v1/models")
    assert calls[1] == ("post", "https://api.example.com/v1/chat/completions", "grok-4.3")


@pytest.mark.asyncio
async def test_doctor_uses_responses_endpoint_for_xai_mode(monkeypatch):
    monkeypatch.setenv("SMART_SEARCH_API_URL", "https://api.x.ai/v1")
    monkeypatch.setenv("SMART_SEARCH_API_KEY", "sk-test-secret")
    calls = []

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, headers, json):
            calls.append((url, json))
            return httpx.Response(
                200,
                json={"output": [{"content": [{"type": "output_text", "text": "ok"}]}]},
                request=httpx.Request("POST", url),
            )

    monkeypatch.setattr(service.httpx, "AsyncClient", FakeAsyncClient)

    result = await service.doctor()

    assert result["ok"] is True
    assert result["primary_api_mode"] == "xai-responses"
    assert result["primary_api_mode_source"] == "default"
    assert result["primary_connection_test"]["status"] == "ok"
    assert calls[0][0] == "https://api.x.ai/v1/responses"
    assert "tools" not in calls[0][1]


@pytest.mark.asyncio
async def test_doctor_tests_main_providers_independently(monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "xai-test-secret")
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_URL", "https://relay.example.com/v1")
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_KEY", "relay-test-secret")
    monkeypatch.setenv("EXA_API_KEY", "exa-test-secret")
    monkeypatch.setenv("TAVILY_API_KEY", "tavily-test-secret")

    async def fake_xai(api_url, api_key, model):
        raise httpx.TimeoutException("xai timeout")

    async def fake_openai(api_url, api_key, model):
        return {"status": "ok", "message": "relay ok"}

    monkeypatch.setattr(service, "_test_primary_responses", fake_xai)
    monkeypatch.setattr(service, "_test_primary_connection", fake_openai)
    async def fake_exa_connection():
        return {"status": "ok", "message": "exa ok"}

    async def fake_tavily_connection():
        return {"status": "ok", "message": "tavily ok"}

    monkeypatch.setattr(service, "_test_exa_connection", fake_exa_connection)
    monkeypatch.setattr(service, "_test_tavily_connection", fake_tavily_connection)

    result = await service.doctor()

    assert result["ok"] is True
    assert result["primary_connection_test"]["status"] == "timeout"
    assert result["main_search_connection_tests"]["xai-responses"]["status"] == "timeout"
    assert result["main_search_connection_tests"]["openai-compatible"]["status"] == "ok"
