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
        "EXA_API_KEY",
        "EXA_BASE_URL",
        "TAVILY_API_KEY",
        "TAVILY_API_URL",
        "FIRECRAWL_API_KEY",
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

    result = await service.search("what is example", extra_sources=1)

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
