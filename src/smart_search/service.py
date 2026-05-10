import asyncio
import json
import time
from pathlib import Path
from typing import Any

import httpx

from .config import config
from .logger import log_info
from .providers.exa import ExaSearchProvider
from .providers.openai_compatible import OpenAICompatibleSearchProvider
from .providers.xai_responses import XAIResponsesSearchProvider
from .sources import merge_sources, new_session_id, split_answer_and_sources


_AVAILABLE_MODELS_CACHE: dict[tuple[str, str], list[str]] = {}
_AVAILABLE_MODELS_LOCK = asyncio.Lock()


def _elapsed_ms(start: float) -> float:
    return round((time.time() - start) * 1000, 2)


async def fetch_available_models(api_url: str, api_key: str) -> list[str]:
    models_url = f"{api_url.rstrip('/')}/models"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            models_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
        data = response.json()

    models: list[str] = []
    for item in (data or {}).get("data", []) or []:
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            models.append(item["id"])
    return models


async def get_available_models_cached(api_url: str, api_key: str) -> list[str]:
    key = (api_url, api_key)
    async with _AVAILABLE_MODELS_LOCK:
        if key in _AVAILABLE_MODELS_CACHE:
            return _AVAILABLE_MODELS_CACHE[key]

    try:
        models = await fetch_available_models(api_url, api_key)
    except Exception:
        models = []

    async with _AVAILABLE_MODELS_LOCK:
        _AVAILABLE_MODELS_CACHE[key] = models
    return models


def extra_results_to_sources(
    tavily_results: list[dict] | None,
    firecrawl_results: list[dict] | None,
) -> list[dict]:
    sources: list[dict] = []
    seen: set[str] = set()

    if firecrawl_results:
        for r in firecrawl_results:
            url = (r.get("url") or "").strip()
            if not url or url in seen:
                continue
            seen.add(url)
            item: dict = {"url": url, "provider": "firecrawl"}
            title = (r.get("title") or "").strip()
            if title:
                item["title"] = title
            desc = (r.get("description") or "").strip()
            if desc:
                item["description"] = desc
            sources.append(item)

    if tavily_results:
        for r in tavily_results:
            url = (r.get("url") or "").strip()
            if not url or url in seen:
                continue
            seen.add(url)
            item = {"url": url, "provider": "tavily"}
            title = (r.get("title") or "").strip()
            if title:
                item["title"] = title
            content = (r.get("content") or "").strip()
            if content:
                item["description"] = content
            sources.append(item)

    return sources


async def call_tavily_extract(url: str) -> str | None:
    api_key = config.tavily_api_key
    if not api_key:
        return None
    endpoint = f"{config.tavily_api_url.rstrip('/')}/extract"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {"urls": [url], "format": "markdown"}
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(endpoint, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()
            if data.get("results") and len(data["results"]) > 0:
                content = data["results"][0].get("raw_content", "")
                return content if content and content.strip() else None
            return None
    except Exception:
        return None


async def call_tavily_search(query: str, max_results: int = 6) -> list[dict] | None:
    api_key = config.tavily_api_key
    if not api_key:
        return None
    endpoint = f"{config.tavily_api_url.rstrip('/')}/search"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {
        "query": query,
        "max_results": max_results,
        "search_depth": "advanced",
        "include_raw_content": False,
        "include_answer": False,
    }
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(endpoint, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", ""),
                    "score": r.get("score", 0),
                }
                for r in results
            ] if results else None
    except Exception:
        return None


async def call_firecrawl_search(query: str, limit: int = 14) -> list[dict] | None:
    api_key = config.firecrawl_api_key
    if not api_key:
        return None
    endpoint = f"{config.firecrawl_api_url.rstrip('/')}/search"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {"query": query, "limit": limit}
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(endpoint, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()
            results = data.get("data", {}).get("web", [])
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "description": r.get("description", ""),
                }
                for r in results
            ] if results else None
    except Exception:
        return None


async def call_firecrawl_scrape(url: str, ctx=None) -> str | None:
    api_key = config.firecrawl_api_key
    if not api_key:
        return None
    endpoint = f"{config.firecrawl_api_url.rstrip('/')}/scrape"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    for attempt in range(config.retry_max_attempts):
        body = {
            "url": url,
            "formats": ["markdown"],
            "timeout": 60000,
            "waitFor": (attempt + 1) * 1500,
        }
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(endpoint, headers=headers, json=body)
                response.raise_for_status()
                data = response.json()
                markdown = data.get("data", {}).get("markdown", "")
                if markdown and markdown.strip():
                    return markdown
                await log_info(ctx, f"Firecrawl: markdown为空, 重试 {attempt + 1}/{config.retry_max_attempts}", config.debug_enabled)
        except Exception as e:
            await log_info(ctx, f"Firecrawl error: {e}", config.debug_enabled)
            return None
    return None


async def call_tavily_map(
    url: str,
    instructions: str = "",
    max_depth: int = 1,
    max_breadth: int = 20,
    limit: int = 50,
    timeout: int = 150,
) -> dict[str, Any]:
    api_key = config.tavily_api_key
    if not api_key:
        return {
            "ok": False,
            "error_type": "config_error",
            "error": "TAVILY_API_KEY 未配置。请运行 `smart-search setup`，或使用 `smart-search config set TAVILY_API_KEY <key>`。",
        }

    endpoint = f"{config.tavily_api_url.rstrip('/')}/map"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {"url": url, "max_depth": max_depth, "max_breadth": max_breadth, "limit": limit, "timeout": timeout}
    if instructions:
        body["instructions"] = instructions
    try:
        async with httpx.AsyncClient(timeout=float(timeout + 10)) as client:
            response = await client.post(endpoint, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()
            return {
                "ok": True,
                "base_url": data.get("base_url", ""),
                "results": data.get("results", []),
                "response_time": data.get("response_time", 0),
            }
    except httpx.TimeoutException:
        return {"ok": False, "error_type": "network_error", "error": f"映射超时: 请求超过{timeout}秒"}
    except httpx.HTTPStatusError as e:
        return {"ok": False, "error_type": "network_error", "error": f"HTTP错误: {e.response.status_code} - {e.response.text[:200]}"}
    except Exception as e:
        return {"ok": False, "error_type": "network_error", "error": f"映射错误: {str(e)}"}


async def search(query: str, platform: str = "", model: str = "", extra_sources: int = 0) -> dict[str, Any]:
    start = time.time()
    session_id = new_session_id()
    try:
        api_url = config.smart_search_api_url
        api_key = config.smart_search_api_key
    except ValueError as e:
        return {
            "ok": False,
            "error_type": "config_error",
            "error": str(e),
            "session_id": session_id,
            "query": query,
            "primary_api_mode": config.smart_search_api_mode,
            "content": "",
            "sources": [],
            "sources_count": 0,
            "elapsed_ms": _elapsed_ms(start),
        }

    try:
        primary_api_mode = config.resolve_primary_api_mode(api_url)
        xai_tools = config.parse_xai_tools() if primary_api_mode == "xai-responses" else []
    except ValueError as e:
        return {
            "ok": False,
            "error_type": "parameter_error",
            "error": str(e),
            "session_id": session_id,
            "query": query,
            "primary_api_mode": config.smart_search_api_mode,
            "content": "",
            "sources": [],
            "sources_count": 0,
            "elapsed_ms": _elapsed_ms(start),
        }

    effective_model = config.smart_search_model
    if model:
        available = await get_available_models_cached(api_url, api_key)
        if available and model not in available:
            return {
                "ok": False,
                "error_type": "parameter_error",
                "error": f"无效模型: {model}",
                "session_id": session_id,
                "query": query,
                "primary_api_mode": primary_api_mode,
                "content": "",
                "sources": [],
                "sources_count": 0,
                "elapsed_ms": _elapsed_ms(start),
            }
        effective_model = model

    if primary_api_mode == "xai-responses":
        search_provider = XAIResponsesSearchProvider(api_url, api_key, effective_model, xai_tools)
    else:
        search_provider = OpenAICompatibleSearchProvider(api_url, api_key, effective_model)

    has_tavily = bool(config.tavily_api_key)
    has_firecrawl = bool(config.firecrawl_api_key)
    tavily_count = 0
    firecrawl_count = 0
    if extra_sources > 0:
        if has_tavily and has_firecrawl:
            tavily_count = max(1, round(extra_sources * 0.6))
            firecrawl_count = extra_sources - tavily_count
        elif has_tavily:
            tavily_count = extra_sources
        elif has_firecrawl:
            firecrawl_count = extra_sources

    coros: list[Any] = [search_provider.search(query, platform)]
    if tavily_count:
        coros.append(call_tavily_search(query, tavily_count))
    if firecrawl_count:
        coros.append(call_firecrawl_search(query, firecrawl_count))

    gathered = await asyncio.gather(*coros, return_exceptions=True)
    primary_result = gathered[0]
    if isinstance(primary_result, BaseException):
        return _primary_search_exception_result(start, session_id, query, primary_api_mode, search_provider.get_provider_name(), primary_result)
    primary_result = primary_result or ""
    tavily_results: list[dict] | None = None
    firecrawl_results: list[dict] | None = None
    idx = 1
    if tavily_count:
        tavily_results = None if isinstance(gathered[idx], BaseException) else gathered[idx]
        idx += 1
    if firecrawl_count:
        firecrawl_results = None if isinstance(gathered[idx], BaseException) else gathered[idx]

    answer, primary_sources = split_answer_and_sources(primary_result)
    sources = merge_sources(primary_sources, extra_results_to_sources(tavily_results, firecrawl_results))
    ok = bool(answer or sources)
    return {
        "ok": ok,
        "error_type": "" if ok else "network_error",
        "error": "" if ok else "搜索失败或无结果",
        "session_id": session_id,
        "query": query,
        "platform": platform,
        "model": effective_model,
        "primary_api_mode": primary_api_mode,
        "content": answer,
        "sources": sources,
        "sources_count": len(sources),
        "elapsed_ms": _elapsed_ms(start),
    }


def _primary_search_exception_result(
    start: float,
    session_id: str,
    query: str,
    primary_api_mode: str,
    provider_name: str,
    exc: BaseException,
) -> dict[str, Any]:
    if isinstance(exc, httpx.TimeoutException):
        return _primary_search_error_result(
            start,
            session_id,
            query,
            primary_api_mode,
            "network_error",
            f"{provider_name} 请求超时: {str(exc)}",
        )
    if isinstance(exc, httpx.HTTPStatusError):
        body = exc.response.text[:300] if exc.response is not None else str(exc)
        status = exc.response.status_code if exc.response is not None else "unknown"
        return _primary_search_error_result(
            start,
            session_id,
            query,
            primary_api_mode,
            "network_error",
            f"{provider_name} HTTP {status}: {body}",
        )
    if isinstance(exc, httpx.RequestError):
        return _primary_search_error_result(
            start,
            session_id,
            query,
            primary_api_mode,
            "network_error",
            f"{provider_name} 网络错误: {str(exc)}",
        )
    return _primary_search_error_result(
        start,
        session_id,
        query,
        primary_api_mode,
        "runtime_error",
        f"{provider_name} 运行错误: {str(exc)}",
    )


def _primary_search_error_result(
    start: float,
    session_id: str,
    query: str,
    primary_api_mode: str,
    error_type: str,
    error: str,
) -> dict[str, Any]:
    return {
        "ok": False,
        "error_type": error_type,
        "error": error,
        "session_id": session_id,
        "query": query,
        "primary_api_mode": primary_api_mode,
        "content": "",
        "sources": [],
        "sources_count": 0,
        "elapsed_ms": _elapsed_ms(start),
    }


async def fetch(url: str) -> dict[str, Any]:
    start = time.time()
    tavily_result = await call_tavily_extract(url)
    if tavily_result:
        return {"ok": True, "url": url, "provider": "tavily", "content": tavily_result, "elapsed_ms": _elapsed_ms(start)}

    firecrawl_result = await call_firecrawl_scrape(url)
    if firecrawl_result:
        return {"ok": True, "url": url, "provider": "firecrawl", "content": firecrawl_result, "elapsed_ms": _elapsed_ms(start)}

    if not config.tavily_api_key and not config.firecrawl_api_key:
        error = "TAVILY_API_KEY 和 FIRECRAWL_API_KEY 均未配置"
        error_type = "config_error"
    else:
        error = "所有提取服务均未能获取内容"
        error_type = "network_error"
    return {"ok": False, "url": url, "provider": "", "content": "", "error_type": error_type, "error": error, "elapsed_ms": _elapsed_ms(start)}


async def map_site(
    url: str,
    instructions: str = "",
    max_depth: int = 1,
    max_breadth: int = 20,
    limit: int = 50,
    timeout: int = 150,
) -> dict[str, Any]:
    start = time.time()
    result = await call_tavily_map(url, instructions, max_depth, max_breadth, limit, timeout)
    result.setdefault("url", url)
    result.setdefault("elapsed_ms", _elapsed_ms(start))
    return result


async def exa_search(
    query: str,
    num_results: int = 5,
    search_type: str = "neural",
    include_text: bool = False,
    include_highlights: bool = False,
    start_published_date: str = "",
    include_domains: str = "",
    exclude_domains: str = "",
    category: str = "",
) -> dict[str, Any]:
    api_key = config.exa_api_key
    if not api_key:
        return {
            "ok": False,
            "error_type": "config_error",
            "error": "EXA_API_KEY 未配置。请运行 `smart-search setup`，或使用 `smart-search config set EXA_API_KEY <key>`。",
        }

    provider = ExaSearchProvider(config.exa_base_url, api_key, config.exa_timeout)
    include_domain_list = [d.strip() for d in include_domains.split(",") if d.strip()] if include_domains else None
    exclude_domain_list = [d.strip() for d in exclude_domains.split(",") if d.strip()] if exclude_domains else None

    raw = await provider.search(
        query=query,
        num_results=num_results,
        search_type=search_type,
        include_text=include_text,
        include_highlights=include_highlights,
        start_published_date=start_published_date or None,
        include_domains=include_domain_list,
        exclude_domains=exclude_domain_list,
        category=category or None,
    )
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {"ok": False, "error_type": "parse_error", "error": raw}
    if not data.get("ok", False):
        data.setdefault("error_type", "network_error")
    return data


async def exa_find_similar(url: str, num_results: int = 5) -> dict[str, Any]:
    api_key = config.exa_api_key
    if not api_key:
        return {
            "ok": False,
            "error_type": "config_error",
            "error": "EXA_API_KEY 未配置。请运行 `smart-search setup`，或使用 `smart-search config set EXA_API_KEY <key>`。",
        }

    provider = ExaSearchProvider(config.exa_base_url, api_key, config.exa_timeout)
    raw = await provider.find_similar(url=url, num_results=num_results)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {"ok": False, "error_type": "parse_error", "error": raw}
    if not data.get("ok", False):
        data.setdefault("error_type", "network_error")
    return data


async def _test_primary_chat_completion(api_url: str, api_key: str, model: str) -> dict[str, Any]:
    chat_url = f"{api_url.rstrip('/')}/chat/completions"
    start = time.time()
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            chat_url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Reply with exactly: ok"}],
                "stream": False,
                "max_tokens": 8,
            },
        )
        response_time = _elapsed_ms(start)
        if response.status_code != 200:
            return {"status": "warning", "message": f"HTTP {response.status_code}: {response.text[:100]}", "response_time_ms": response_time}
        return {"status": "ok", "message": f"聊天接口可用 (HTTP {response.status_code})", "response_time_ms": response_time}


async def _test_primary_connection(api_url: str, api_key: str, model: str) -> dict[str, Any]:
    models_url = f"{api_url.rstrip('/')}/models"
    start = time.time()
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            models_url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        )
        response_time = _elapsed_ms(start)
        if response.status_code != 200:
            models_test = {"status": "warning", "message": f"HTTP {response.status_code}: {response.text[:100]}", "response_time_ms": response_time}
            chat_test = await _test_primary_chat_completion(api_url, api_key, model)
            if chat_test.get("status") == "ok":
                return {
                    "status": "ok",
                    "message": f"{chat_test['message']}；模型列表接口不可用: {models_test['message']}",
                    "response_time_ms": chat_test.get("response_time_ms"),
                    "models_endpoint_test": models_test,
                    "chat_completion_test": chat_test,
                }
            return {
                "status": "warning",
                "message": f"模型列表接口不可用: {models_test['message']}；聊天接口不可用: {chat_test.get('message', '')}",
                "response_time_ms": chat_test.get("response_time_ms", response_time),
                "models_endpoint_test": models_test,
                "chat_completion_test": chat_test,
            }
        result: dict[str, Any] = {"status": "ok", "message": f"成功获取模型列表 (HTTP {response.status_code})", "response_time_ms": response_time}
        try:
            models_data = response.json()
            model_names = [m["id"] for m in models_data.get("data", []) if isinstance(m, dict) and "id" in m]
            result["message"] += f"，共 {len(model_names)} 个模型"
            if model_names:
                result["available_models"] = model_names
        except Exception:
            pass
        return result


async def _test_primary_responses(api_url: str, api_key: str, model: str) -> dict[str, Any]:
    responses_url = f"{api_url.rstrip('/')}/responses"
    start = time.time()
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            responses_url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "input": [{"role": "user", "content": "Reply with exactly: ok"}],
                "stream": False,
            },
        )
        response_time = _elapsed_ms(start)
        if response.status_code != 200:
            return {"status": "warning", "message": f"HTTP {response.status_code}: {response.text[:100]}", "response_time_ms": response_time}
        return {"status": "ok", "message": f"xAI Responses API 可用 (HTTP {response.status_code})", "response_time_ms": response_time}


async def _test_exa_connection() -> dict[str, Any]:
    exa_key = config.exa_api_key
    if not exa_key:
        return {"status": "not_configured", "message": "EXA_API_KEY 未设置，Exa 搜索功能不可用"}
    start = time.time()
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{config.exa_base_url.rstrip('/')}/search",
            headers={"x-api-key": exa_key, "content-type": "application/json"},
            json={"query": "test", "numResults": 1, "type": "keyword"},
        )
        response_time = _elapsed_ms(start)
        if resp.status_code == 200:
            return {"status": "ok", "message": "Exa API 可用 (HTTP 200)", "response_time_ms": response_time}
        return {"status": "warning", "message": f"HTTP {resp.status_code}: {resp.text[:100]}", "response_time_ms": response_time}


async def _test_tavily_connection() -> dict[str, Any]:
    tavily_key = config.tavily_api_key
    if not tavily_key:
        return {"status": "not_configured", "message": "TAVILY_API_KEY 未设置，Tavily 功能不可用"}
    start = time.time()
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{config.tavily_api_url.rstrip('/')}/search",
            headers={"Authorization": f"Bearer {tavily_key}", "Content-Type": "application/json"},
            json={"query": "test", "max_results": 1, "search_depth": "basic"},
        )
        response_time = _elapsed_ms(start)
        if resp.status_code == 200:
            return {"status": "ok", "message": "Tavily API 可用 (HTTP 200)", "response_time_ms": response_time}
        return {"status": "warning", "message": f"HTTP {resp.status_code}: {resp.text[:100]}", "response_time_ms": response_time}


async def doctor() -> dict[str, Any]:
    info = config.get_config_info()

    try:
        api_url = config.smart_search_api_url
        api_key = config.smart_search_api_key
        model = config.smart_search_model
        primary_api_mode = config.resolve_primary_api_mode(api_url)
        info["primary_api_mode"] = primary_api_mode
        if primary_api_mode == "xai-responses":
            info["primary_connection_test"] = await _test_primary_responses(api_url, api_key, model)
        else:
            info["primary_connection_test"] = await _test_primary_connection(api_url, api_key, model)
    except httpx.TimeoutException:
        info["primary_connection_test"] = {"status": "timeout", "message": "请求超时（10秒），请检查网络连接或 API URL"}
    except httpx.RequestError as e:
        info["primary_connection_test"] = {"status": "error", "message": f"网络错误: {str(e)}"}
    except ValueError as e:
        info["primary_connection_test"] = {"status": "config_error", "message": str(e)}
    except Exception as e:
        info["primary_connection_test"] = {"status": "error", "message": f"未知错误: {str(e)}"}

    try:
        info["exa_connection_test"] = await _test_exa_connection()
    except httpx.TimeoutException:
        info["exa_connection_test"] = {"status": "timeout", "message": "Exa API 请求超时"}
    except Exception as e:
        info["exa_connection_test"] = {"status": "error", "message": str(e)}

    try:
        info["tavily_connection_test"] = await _test_tavily_connection()
    except httpx.TimeoutException:
        info["tavily_connection_test"] = {"status": "timeout", "message": "Tavily API 请求超时"}
    except Exception as e:
        info["tavily_connection_test"] = {"status": "error", "message": str(e)}

    if config.firecrawl_api_key:
        info["firecrawl_connection_test"] = {"status": "configured", "message": "FIRECRAWL_API_KEY 已设置"}
    else:
        info["firecrawl_connection_test"] = {"status": "not_configured", "message": "FIRECRAWL_API_KEY 未设置，Firecrawl 功能不可用"}

    primary_test = info.get("primary_connection_test", {})
    primary_status = primary_test.get("status")
    info["ok"] = primary_status == "ok"
    if info["ok"]:
        info["error_type"] = ""
        info["error"] = ""
    else:
        info["error"] = primary_test.get("message", "Primary connection check failed")
        if primary_status == "config_error":
            info["error_type"] = "config_error"
        elif primary_status in {"timeout", "error", "warning"}:
            info["error_type"] = "network_error"
        else:
            info["error_type"] = "runtime_error"
    return info


def current_model() -> dict[str, Any]:
    return {"ok": True, "model": config.smart_search_model, "config_file": str(config.config_file)}


def set_model(model: str) -> dict[str, Any]:
    previous = config.smart_search_model
    config.set_model(model)
    return {"ok": True, "previous_model": previous, "current_model": config.smart_search_model, "config_file": str(config.config_file)}


def config_path() -> dict[str, Any]:
    return config.config_path_info()


def config_list(show_secrets: bool = False) -> dict[str, Any]:
    return {
        "ok": True,
        "config_file": str(config.config_file),
        "values": config.get_saved_config(masked=not show_secrets),
    }


def config_set(key: str, value: str) -> dict[str, Any]:
    config.set_config_value(key, value)
    saved = config.get_saved_config(masked=True)
    return {
        "ok": True,
        "config_file": str(config.config_file),
        "key": key.strip().upper(),
        "value": saved.get(key.strip().upper(), ""),
    }


def config_unset(key: str) -> dict[str, Any]:
    config.unset_config_value(key)
    return {"ok": True, "config_file": str(config.config_file), "key": key.strip().upper()}


def write_output(path: str | Path, content: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
