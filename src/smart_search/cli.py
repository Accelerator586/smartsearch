import argparse
import asyncio
import getpass
import json
from importlib import metadata
import subprocess
import sys
from pathlib import Path
from typing import Any

from . import service


EXIT_OK = 0
EXIT_PARAMETER_ERROR = 2
EXIT_CONFIG_ERROR = 3
EXIT_NETWORK_ERROR = 4
EXIT_RUNTIME_ERROR = 5

COMMAND_ALIASES = {
    "search": ["s"],
    "fetch": ["f"],
    "map": ["m"],
    "exa-search": ["exa", "x"],
    "exa-similar": ["xs"],
    "zhipu-search": ["z", "zp"],
    "context7-library": ["c7", "ctx7"],
    "context7-docs": ["c7d", "c7docs", "ctx7-docs"],
    "smoke": ["sm"],
    "doctor": ["d"],
    "model": ["mdl"],
    "setup": ["init"],
    "config": ["cfg"],
    "regression": ["reg"],
}

CONFIG_COMMAND_ALIASES = {
    "path": ["p"],
    "list": ["ls", "l"],
    "set": ["s"],
    "unset": ["rm", "u"],
}

MODEL_COMMAND_ALIASES = {
    "set": ["s"],
    "current": ["cur", "c"],
}


def _get_version() -> str:
    root = Path(__file__).resolve().parents[2]
    package_json = root / "package.json"
    try:
        version = json.loads(package_json.read_text(encoding="utf-8")).get("version", "")
        if version:
            return str(version)
    except (OSError, json.JSONDecodeError):
        pass

    pyproject = root / "pyproject.toml"
    try:
        for line in pyproject.read_text(encoding="utf-8").splitlines():
            if line.startswith("version = "):
                return line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass

    try:
        return metadata.version("smart-search")
    except metadata.PackageNotFoundError:
        pass

    return "unknown"


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=True, indent=2)


def _format_seconds(seconds: float) -> str:
    return f"{seconds:g}"


def _search_timeout_result(query: str, timeout: float) -> dict[str, Any]:
    seconds = _format_seconds(timeout)
    return {
        "ok": False,
        "error_type": "network_error",
        "error": f"Search timed out after {seconds} seconds",
        "query": query,
        "content": "",
        "sources": [],
        "sources_count": 0,
        "primary_sources": [],
        "primary_sources_count": 0,
        "extra_sources": [],
        "extra_sources_count": 0,
        "source_warning": "",
        "routing_decision": {},
        "providers_used": [],
        "provider_attempts": [],
        "fallback_used": False,
        "validation_level": "",
        "timeout_seconds": timeout,
    }


def _format_markdown(command: str, data: dict[str, Any]) -> str:
    if command == "search":
        lines = [data.get("content", "")]
        primary_sources = data.get("primary_sources") or []
        extra_sources = data.get("extra_sources") or []
        if primary_sources or extra_sources:
            warning = data.get("source_warning") or ""
            if warning:
                lines.append(f"\n> {warning}")
            if primary_sources:
                lines.append("\n## Primary Sources")
                for item in primary_sources:
                    url = item.get("url", "")
                    title = item.get("title") or item.get("provider") or url
                    lines.append(f"- [{title}]({url})")
            if extra_sources:
                lines.append("\n## Extra Sources")
                for item in extra_sources:
                    url = item.get("url", "")
                    title = item.get("title") or item.get("provider") or url
                    lines.append(f"- [{title}]({url})")
            return "\n".join(lines).strip() + "\n"

        sources = data.get("sources") or []
        if sources:
            lines.append("\n## Sources")
            for item in sources:
                url = item.get("url", "")
                title = item.get("title") or item.get("provider") or url
                lines.append(f"- [{title}]({url})")
        return "\n".join(lines).strip() + "\n"
    if command == "fetch":
        return (data.get("content") or "") + ("\n" if data.get("content") else "")
    return _json(data)


def _render(command: str, data: dict[str, Any], fmt: str) -> str:
    if fmt == "markdown":
        return _format_markdown(command, data)
    return _json(data)


def _stdout_safe(text: str) -> str:
    return _stream_safe(sys.stdout, text)


def _stream_safe(stream: Any, text: str) -> str:
    encoding = getattr(stream, "encoding", None) or "utf-8"
    errors = getattr(stream, "errors", None) or "strict"
    try:
        text.encode(encoding, errors=errors)
        return text
    except UnicodeEncodeError:
        return text.encode(encoding, errors="backslashreplace").decode(encoding)


def _write_stdout(text: str) -> None:
    sys.stdout.write(_stdout_safe(text))


def _write_stderr(text: str) -> None:
    sys.stderr.write(_stream_safe(sys.stderr, text))


def _exit_code(data: dict[str, Any]) -> int:
    if data.get("ok", False):
        return EXIT_OK
    error_type = data.get("error_type")
    if error_type == "config_error":
        return EXIT_CONFIG_ERROR
    if error_type == "parameter_error":
        return EXIT_PARAMETER_ERROR
    if error_type == "network_error":
        return EXIT_NETWORK_ERROR
    if error_type == "evidence_error":
        return EXIT_NETWORK_ERROR
    return EXIT_RUNTIME_ERROR


def _print_result(command: str, data: dict[str, Any], fmt: str, output: str = "") -> int:
    rendered = _render(command, data, fmt)
    if output:
        service.write_output(output, rendered)
    _write_stdout(rendered)
    if rendered and not rendered.endswith("\n"):
        _write_stdout("\n")
    return _exit_code(data)


def _add_format_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--output", default="", help="Write rendered output to a file.")


def _is_secret_key(key: str) -> bool:
    upper_key = key.upper()
    return "KEY" in upper_key or "TOKEN" in upper_key or "SECRET" in upper_key


def _t(lang: str, zh: str, en: str) -> str:
    return zh if lang == "zh" else en


def _display_provider(provider: str, lang: str) -> str:
    names = {
        "xai-responses": "xAI Responses",
        "openai-compatible": "OpenAI-compatible",
        "zhipu": _t(lang, "智谱", "Zhipu"),
        "exa": "Exa",
        "context7": "Context7",
        "tavily": "Tavily",
        "firecrawl": "Firecrawl",
    }
    return names.get(provider, provider)


def _setup_status_from_values(values: dict[str, str]) -> dict[str, Any]:
    def has(key: str) -> bool:
        return bool(values.get(key))

    main_configured: set[str] = set()
    if has("XAI_API_KEY"):
        main_configured.add("xai-responses")
    if has("OPENAI_COMPATIBLE_API_URL") and has("OPENAI_COMPATIBLE_API_KEY"):
        main_configured.add("openai-compatible")
    if has("SMART_SEARCH_API_URL") and has("SMART_SEARCH_API_KEY"):
        mode = (values.get("SMART_SEARCH_API_MODE") or "auto").strip().lower()
        legacy_url = values.get("SMART_SEARCH_API_URL", "")
        if mode == "xai-responses" or (mode == "auto" and "api.x.ai" in legacy_url.lower()):
            main_configured.add("xai-responses")
        else:
            main_configured.add("openai-compatible")

    status = {
        "main_search": {
            "configured": [provider for provider in ("xai-responses", "openai-compatible") if provider in main_configured],
            "fallback_chain": ["xai-responses", "openai-compatible"],
        },
        "web_search": {
            "configured": [
                provider
                for provider, configured in [
                    ("zhipu", has("ZHIPU_API_KEY")),
                    ("tavily", has("TAVILY_API_KEY")),
                    ("firecrawl", has("FIRECRAWL_API_KEY")),
                ]
                if configured
            ],
            "fallback_chain": ["zhipu", "tavily", "firecrawl"],
        },
        "docs_search": {
            "configured": [
                provider
                for provider, configured in [
                    ("exa", has("EXA_API_KEY")),
                    ("context7", has("CONTEXT7_API_KEY")),
                ]
                if configured
            ],
            "fallback_chain": ["exa", "context7"],
        },
        "web_fetch": {
            "configured": [
                provider
                for provider, configured in [
                    ("tavily", has("TAVILY_API_KEY")),
                    ("firecrawl", has("FIRECRAWL_API_KEY")),
                ]
                if configured
            ],
            "fallback_chain": ["tavily", "firecrawl"],
        },
    }
    for item in status.values():
        item["ok"] = bool(item["configured"])
    return status


def _merge_setup_values(current: dict[str, str], values: dict[str, str]) -> dict[str, str]:
    merged = dict(current)
    merged.update({key: value for key, value in values.items() if value})
    return merged


def _write_setup_status(status: dict[str, Any], lang: str, *, final: bool = False) -> None:
    title = _t(lang, "最低配置检查", "Minimum profile check") if final else _t(lang, "当前状态", "Current status")
    _write_stderr(f"\n{title}:\n")
    required = {"main_search", "docs_search", "web_fetch"}
    labels = {
        "main_search": _t(lang, "main_search 主搜索", "main_search primary search"),
        "docs_search": _t(lang, "docs_search 文档搜索", "docs_search documentation search"),
        "web_fetch": _t(lang, "web_fetch 网页抓取", "web_fetch page fetch"),
        "web_search": _t(lang, "web_search 网页补强", "web_search web reinforcement"),
    }
    for capability in ("main_search", "docs_search", "web_fetch", "web_search"):
        item = status.get(capability, {})
        configured = item.get("configured") or []
        configured_text = ", ".join(_display_provider(provider, lang) for provider in configured)
        if item.get("ok"):
            marker = "OK"
            value = configured_text
        elif capability in required:
            marker = "MISSING"
            value = _t(lang, "需要至少配置一个 provider", "at least one provider is required")
        else:
            marker = "OPTIONAL"
            value = _t(lang, "未配置", "not configured")
        _write_stderr(f"  [{marker}] {labels[capability]}: {value}\n")


def _prompt_choice(prompt: str, default: str = "") -> str:
    _write_stderr(prompt)
    value = input("").strip()
    return value or default


def _prompt_yes_no(prompt: str, default: bool = False) -> bool:
    default_text = "Y/n" if default else "y/N"
    answer = _prompt_choice(f"{prompt} [{default_text}]: ", "y" if default else "n").strip().lower()
    return answer in {"y", "yes", "是", "好", "1", "true"}


def _prompt_value(key: str, label: str, current: str = "", optional: bool = False, lang: str = "en") -> str:
    suffix = _t(lang, " 可选", " optional") if optional else _t(lang, " 必填", " required")
    current_display = _t(lang, "已配置", "configured") if current and _is_secret_key(key) else current
    if current:
        prompt = f"{label}{suffix} [{current_display}]: "
    else:
        prompt = f"{label}{suffix}: "
    if _is_secret_key(key):
        value = getpass.getpass(_stream_safe(sys.stderr, prompt)).strip()
    else:
        _write_stderr(prompt)
        value = input("").strip()
    return value or current


def _select_setup_language(lang: str = "") -> str:
    if lang in {"zh", "en"}:
        return lang
    answer = _prompt_choice("Language / 语言 [zh/en] (zh): ", "zh").strip().lower()
    if answer in {"en", "english"}:
        return "en"
    return "zh"


def _setup_choice(prompt: str, choices: set[str], default: str) -> str:
    value = _prompt_choice(prompt, default).strip().lower()
    aliases = {
        "保持": "keep",
        "跳过": "skip",
        "都配": "both",
        "两个": "both",
        "是": "yes",
        "否": "no",
    }
    value = aliases.get(value, value)
    return value if value in choices else default


def _prompt_main_search(values: dict[str, str], current: dict[str, str], lang: str) -> None:
    status = _setup_status_from_values(_merge_setup_values(current, values))
    configured = status["main_search"]["configured"]
    default = "keep" if configured else "xai"
    _write_stderr(
        _t(
            lang,
            "\n[1/3 必选] main_search 主搜索\n用途: 负责综合搜索回答和最终合成。\n推荐: 有 xAI key 选 xai；有中转服务选 openai；两者都配可以同能力兜底。\n",
            "\n[1/3 Required] main_search primary search\nPurpose: broad search answers and final synthesis.\nRecommended: choose xai for an xAI key, openai for a relay, or both for same-capability fallback.\n",
        )
    )
    if current.get("SMART_SEARCH_API_URL") and current.get("SMART_SEARCH_API_KEY"):
        _write_stderr(
            _t(
                lang,
                "提示: 检测到 legacy 主搜索配置仍可用；建议后续迁移到 XAI_* 或 OPENAI_COMPATIBLE_*。\n",
                "Note: legacy primary search config is available; consider migrating to XAI_* or OPENAI_COMPATIBLE_* later.\n",
            )
        )
    choice = _setup_choice(
        _t(
            lang,
            f"选择主搜索 provider [keep/xai/openai/both/skip] ({default}): ",
            f"Choose main search provider [keep/xai/openai/both/skip] ({default}): ",
        ),
        {"keep", "xai", "openai", "both", "skip"},
        default,
    )
    if choice in {"keep", "skip"}:
        return
    if choice in {"xai", "both"}:
        values["XAI_API_KEY"] = _prompt_value("XAI_API_KEY", "xAI API key", current.get("XAI_API_KEY", ""), lang=lang)
        values["XAI_MODEL"] = _prompt_value(
            "XAI_MODEL",
            _t(lang, "xAI Responses 模型", "xAI Responses model"),
            current.get("XAI_MODEL", ""),
            optional=True,
            lang=lang,
        )
    if choice in {"openai", "both"}:
        values["OPENAI_COMPATIBLE_API_URL"] = _prompt_value(
            "OPENAI_COMPATIBLE_API_URL",
            _t(lang, "OpenAI-compatible API 地址", "OpenAI-compatible API URL"),
            current.get("OPENAI_COMPATIBLE_API_URL", ""),
            lang=lang,
        )
        values["OPENAI_COMPATIBLE_API_KEY"] = _prompt_value(
            "OPENAI_COMPATIBLE_API_KEY",
            "OpenAI-compatible API key",
            current.get("OPENAI_COMPATIBLE_API_KEY", ""),
            lang=lang,
        )
        values["OPENAI_COMPATIBLE_MODEL"] = _prompt_value(
            "OPENAI_COMPATIBLE_MODEL",
            _t(lang, "OpenAI-compatible 模型", "OpenAI-compatible model"),
            current.get("OPENAI_COMPATIBLE_MODEL", ""),
            optional=True,
            lang=lang,
        )


def _prompt_docs_search(values: dict[str, str], current: dict[str, str], lang: str) -> None:
    status = _setup_status_from_values(_merge_setup_values(current, values))
    default = "keep" if status["docs_search"]["configured"] else "exa"
    _write_stderr(
        _t(
            lang,
            "\n[2/3 必选] docs_search 文档搜索\n用途: 查官方文档、SDK、API、框架和库说明。\n推荐: Exa 通用性更强；Context7 更专注文档。\n",
            "\n[2/3 Required] docs_search documentation search\nPurpose: official docs, SDKs, APIs, frameworks, and library references.\nRecommended: Exa is broader; Context7 is more documentation-focused.\n",
        )
    )
    choice = _setup_choice(
        _t(
            lang,
            f"选择文档搜索 provider [keep/exa/context7/both/skip] ({default}): ",
            f"Choose docs provider [keep/exa/context7/both/skip] ({default}): ",
        ),
        {"keep", "exa", "context7", "both", "skip"},
        default,
    )
    if choice in {"keep", "skip"}:
        return
    if choice in {"exa", "both"}:
        values["EXA_API_KEY"] = _prompt_value("EXA_API_KEY", "Exa API key", current.get("EXA_API_KEY", ""), lang=lang)
    if choice in {"context7", "both"}:
        values["CONTEXT7_API_KEY"] = _prompt_value(
            "CONTEXT7_API_KEY",
            "Context7 API key",
            current.get("CONTEXT7_API_KEY", ""),
            lang=lang,
        )


def _prompt_web_fetch(values: dict[str, str], current: dict[str, str], lang: str) -> None:
    status = _setup_status_from_values(_merge_setup_values(current, values))
    default = "keep" if status["web_fetch"]["configured"] else "tavily"
    _write_stderr(
        _t(
            lang,
            "\n[3/3 必选] web_fetch 网页抓取\n用途: 已知 URL 抓正文；高风险事实核验必须用。\n推荐: Tavily 优先；Firecrawl 可作为抓取兜底。\n",
            "\n[3/3 Required] web_fetch page fetch\nPurpose: extract known URLs; required for high-risk fact checks.\nRecommended: Tavily first; Firecrawl as fetch fallback.\n",
        )
    )
    choice = _setup_choice(
        _t(
            lang,
            f"选择网页抓取 provider [keep/tavily/firecrawl/both/skip] ({default}): ",
            f"Choose fetch provider [keep/tavily/firecrawl/both/skip] ({default}): ",
        ),
        {"keep", "tavily", "firecrawl", "both", "skip"},
        default,
    )
    if choice in {"keep", "skip"}:
        return
    if choice in {"tavily", "both"}:
        values["TAVILY_API_KEY"] = _prompt_value("TAVILY_API_KEY", "Tavily API key", current.get("TAVILY_API_KEY", ""), lang=lang)
    if choice in {"firecrawl", "both"}:
        values["FIRECRAWL_API_KEY"] = _prompt_value(
            "FIRECRAWL_API_KEY",
            "Firecrawl API key",
            current.get("FIRECRAWL_API_KEY", ""),
            lang=lang,
        )


def _prompt_optional_enhancements(values: dict[str, str], current: dict[str, str], lang: str) -> None:
    _write_stderr(
        _t(
            lang,
            "\n[可选增强] web_search 网页补强\n用途: 中文、国内、时效、域名过滤类来源检索。\n推荐: 中文场景建议配置 Zhipu。\n",
            "\n[Optional] web_search web reinforcement\nPurpose: Chinese, domestic, current, or domain-filtered source discovery.\nRecommended: configure Zhipu for Chinese/current scenarios.\n",
        )
    )
    if _prompt_yes_no(_t(lang, "是否配置 Zhipu API key?", "Configure Zhipu API key?"), default=False):
        values["ZHIPU_API_KEY"] = _prompt_value("ZHIPU_API_KEY", "Zhipu API key", current.get("ZHIPU_API_KEY", ""), lang=lang)
    if _prompt_yes_no(_t(lang, "是否调整验证/兜底默认值?", "Adjust validation/fallback defaults?"), default=False):
        values["SMART_SEARCH_VALIDATION_LEVEL"] = _prompt_value(
            "SMART_SEARCH_VALIDATION_LEVEL",
            _t(lang, "验证强度 (fast/balanced/strict)", "Validation level (fast/balanced/strict)"),
            current.get("SMART_SEARCH_VALIDATION_LEVEL", ""),
            optional=True,
            lang=lang,
        )
        values["SMART_SEARCH_FALLBACK_MODE"] = _prompt_value(
            "SMART_SEARCH_FALLBACK_MODE",
            _t(lang, "兜底模式 (auto/off)", "Fallback mode (auto/off)"),
            current.get("SMART_SEARCH_FALLBACK_MODE", ""),
            optional=True,
            lang=lang,
        )
        values["SMART_SEARCH_MINIMUM_PROFILE"] = _prompt_value(
            "SMART_SEARCH_MINIMUM_PROFILE",
            _t(lang, "最低配置门槛 (standard/off)", "Minimum profile (standard/off)"),
            current.get("SMART_SEARCH_MINIMUM_PROFILE", ""),
            optional=True,
            lang=lang,
        )


def _run_guided_setup_prompts(values: dict[str, str], current: dict[str, str], lang: str) -> None:
    config_file = service.config_path()["config_file"]
    _write_stderr(
        _t(
            lang,
            f"\nSmart Search 配置向导\n配置文件: {config_file}\n\n目标: standard 最低可用配置\n说明: provider 选择处空回车 = 使用括号里的默认项；key 输入处空回车 = 保留当前值或跳过；API Key 输入不会显示。\n\n最低要求:\n  [必选] main_search 主搜索: xAI Responses 或 OpenAI-compatible 至少一个\n  [必选] docs_search 文档/副搜索: Exa 或 Context7 至少一个\n  [必选] web_fetch 网页抓取: Tavily 或 Firecrawl 至少一个\n  [可选] web_search 网页补强: Zhipu / Tavily / Firecrawl\n",
            f"\nSmart Search setup wizard\nConfig file: {config_file}\n\nGoal: standard minimum profile\nNotes: empty Enter on provider choices uses the shown default; empty Enter on key prompts keeps the current value or skips; API key input is hidden.\n\nMinimum requirements:\n  [required] main_search: at least one of xAI Responses or OpenAI-compatible\n  [required] docs_search: at least one of Exa or Context7\n  [required] web_fetch: at least one of Tavily or Firecrawl\n  [optional] web_search reinforcement: Zhipu / Tavily / Firecrawl\n",
        )
    )
    _write_setup_status(_setup_status_from_values(_merge_setup_values(current, values)), lang)
    _prompt_main_search(values, current, lang)
    _prompt_docs_search(values, current, lang)
    _prompt_web_fetch(values, current, lang)
    _prompt_optional_enhancements(values, current, lang)


def _run_advanced_setup_prompts(values: dict[str, str], current: dict[str, str], lang: str) -> None:
    _write_stderr(
        _t(
            lang,
            "\n高级模式: 逐项配置底层键。一般用户建议直接使用默认分组向导。\n",
            "\nAdvanced mode: configure low-level keys one by one. Most users should use the grouped wizard.\n",
        )
    )
    prompts = [
        ("XAI_API_URL", "xAI Responses API URL", True),
        ("XAI_API_KEY", "xAI API key", True),
        ("XAI_MODEL", "xAI Responses model", True),
        ("XAI_TOOLS", "xAI Responses tools (web_search,x_search)", True),
        ("OPENAI_COMPATIBLE_API_URL", "OpenAI-compatible API URL", True),
        ("OPENAI_COMPATIBLE_API_KEY", "OpenAI-compatible API key", True),
        ("OPENAI_COMPATIBLE_MODEL", "OpenAI-compatible model", True),
        ("SMART_SEARCH_API_URL", "Legacy primary API URL", True),
        ("SMART_SEARCH_API_KEY", "Legacy primary API key", True),
        ("SMART_SEARCH_API_MODE", "Legacy primary API mode (auto/xai-responses/chat-completions)", True),
        ("SMART_SEARCH_XAI_TOOLS", "Legacy xAI Responses tools (web_search,x_search)", True),
        ("SMART_SEARCH_MODEL", "Default model", True),
        ("SMART_SEARCH_VALIDATION_LEVEL", "Validation level (fast/balanced/strict)", True),
        ("SMART_SEARCH_FALLBACK_MODE", "Fallback mode (auto/off)", True),
        ("SMART_SEARCH_MINIMUM_PROFILE", "Minimum profile (standard/off)", True),
        ("EXA_API_KEY", "Exa API key", True),
        ("CONTEXT7_API_KEY", "Context7 API key", True),
        ("ZHIPU_API_KEY", "Zhipu API key", True),
        ("TAVILY_API_KEY", "Tavily API key", True),
        ("FIRECRAWL_API_KEY", "Firecrawl API key", True),
    ]
    for key, label, optional in prompts:
        if values[key]:
            continue
        values[key] = _prompt_value(key, label, current.get(key, ""), optional=optional, lang=lang)


async def _run_async(args: argparse.Namespace) -> int:
    if args.command == "search":
        try:
            data = await asyncio.wait_for(
                service.search(
                    args.query,
                    platform=args.platform,
                    model=args.model,
                    extra_sources=args.extra_sources,
                    validation=args.validation,
                    fallback=args.fallback,
                    providers=args.providers,
                ),
                timeout=args.timeout,
            )
        except asyncio.TimeoutError:
            data = _search_timeout_result(args.query, args.timeout)
            return _print_result("search", data, "json", args.output)
        return _print_result("search", data, args.format, args.output)
    if args.command == "fetch":
        data = await service.fetch(args.url)
        return _print_result("fetch", data, args.format, args.output)
    if args.command == "map":
        data = await service.map_site(
            args.url,
            instructions=args.instructions,
            max_depth=args.max_depth,
            max_breadth=args.max_breadth,
            limit=args.limit,
            timeout=args.timeout,
        )
        return _print_result("map", data, args.format, args.output)
    if args.command == "exa-search":
        data = await service.exa_search(
            args.query,
            num_results=args.num_results,
            search_type=args.search_type,
            include_text=args.include_text,
            include_highlights=args.include_highlights,
            start_published_date=args.start_published_date,
            include_domains=args.include_domains,
            exclude_domains=args.exclude_domains,
            category=args.category,
        )
        return _print_result("exa-search", data, args.format, args.output)
    if args.command == "exa-similar":
        data = await service.exa_find_similar(args.url, num_results=args.num_results)
        return _print_result("exa-similar", data, args.format, args.output)
    if args.command == "zhipu-search":
        data = await service.zhipu_search(
            args.query,
            count=args.count,
            search_engine=args.search_engine,
            search_recency_filter=args.search_recency_filter,
            search_domain_filter=args.search_domain_filter,
            content_size=args.content_size,
        )
        return _print_result("zhipu-search", data, args.format, args.output)
    if args.command == "context7-library":
        data = await service.context7_library(args.name, args.query)
        return _print_result("context7-library", data, args.format, args.output)
    if args.command == "context7-docs":
        data = await service.context7_docs(args.library_id, args.query)
        return _print_result("context7-docs", data, args.format, args.output)
    if args.command == "smoke":
        data = await service.smoke(args.mode)
        return _print_result("smoke", data, args.format, args.output)
    if args.command == "doctor":
        data = await service.doctor()
        return _print_result("doctor", data, args.format, args.output)
    return EXIT_PARAMETER_ERROR


def _run_model(args: argparse.Namespace) -> int:
    if args.model_command == "set":
        data = service.set_model(args.model)
    elif args.model_command == "current":
        data = service.current_model()
    else:
        data = {"ok": False, "error_type": "parameter_error", "error": "Unknown model command"}
    return _print_result("model", data, args.format, args.output)


def _run_config(args: argparse.Namespace) -> int:
    if args.config_command == "path":
        data = service.config_path()
    elif args.config_command == "list":
        data = service.config_list(show_secrets=False)
    elif args.config_command == "set":
        data = service.config_set(args.key, args.value)
    elif args.config_command == "unset":
        data = service.config_unset(args.key)
    else:
        data = {"ok": False, "error_type": "parameter_error", "error": "Unknown config command"}
    return _print_result("config", data, args.format, args.output)


def _run_setup(args: argparse.Namespace) -> int:
    values = {
        "SMART_SEARCH_API_URL": args.api_url,
        "SMART_SEARCH_API_KEY": args.api_key,
        "SMART_SEARCH_API_MODE": args.api_mode,
        "SMART_SEARCH_XAI_TOOLS": args.xai_tools,
        "SMART_SEARCH_MODEL": args.model,
        "XAI_API_URL": args.xai_api_url,
        "XAI_API_KEY": args.xai_api_key,
        "XAI_MODEL": args.xai_model,
        "XAI_TOOLS": args.xai_tools_explicit,
        "OPENAI_COMPATIBLE_API_URL": args.openai_compatible_api_url,
        "OPENAI_COMPATIBLE_API_KEY": args.openai_compatible_api_key,
        "OPENAI_COMPATIBLE_MODEL": args.openai_compatible_model,
        "SMART_SEARCH_VALIDATION_LEVEL": args.validation_level,
        "SMART_SEARCH_FALLBACK_MODE": args.fallback_mode,
        "SMART_SEARCH_MINIMUM_PROFILE": args.minimum_profile,
        "EXA_API_KEY": args.exa_key,
        "CONTEXT7_API_KEY": args.context7_key,
        "ZHIPU_API_KEY": args.zhipu_key,
        "TAVILY_API_KEY": args.tavily_key,
        "FIRECRAWL_API_KEY": args.firecrawl_key,
    }

    if not args.non_interactive:
        current = service.config_list(show_secrets=True)["values"]
        lang = _select_setup_language(args.lang)
        if args.advanced:
            _run_advanced_setup_prompts(values, current, lang)
        else:
            _run_guided_setup_prompts(values, current, lang)

    saved: dict[str, str] = {}
    for key, value in values.items():
        if value:
            result = service.config_set(key, value)
            saved[key] = result.get("value", "")

    data = {"ok": True, "config_file": service.config_path()["config_file"], "saved": saved}
    if not args.non_interactive:
        current_after = service.config_list(show_secrets=True)["values"]
        final_values = _merge_setup_values(current_after, values)
        final_status = _setup_status_from_values(final_values)
        _write_stderr(_t(lang, "\n保存完成。\n", "\nSaved.\n"))
        _write_setup_status(final_status, lang, final=True)
        missing = [capability for capability in ("main_search", "docs_search", "web_fetch") if not final_status[capability]["ok"]]
        if missing:
            _write_stderr(
                _t(
                    lang,
                    "\n当前配置尚未满足 standard 最低配置。\nsearch / doctor 会 fail closed，不会假装可用。\n",
                    "\nThe current config does not satisfy the standard minimum profile.\nsearch / doctor will fail closed instead of pretending to work.\n",
                )
            )
        else:
            _write_stderr(
                _t(
                    lang,
                    "\n下一步建议:\n  smart-search doctor --format json\n  smart-search smoke --mock --format json\n",
                    "\nNext steps:\n  smart-search doctor --format json\n  smart-search smoke --mock --format json\n",
                )
            )
        data["minimum_profile_ok"] = not missing
        data["minimum_profile_missing"] = missing
        data["capability_status"] = final_status
    return _print_result("setup", data, args.format, args.output)


def _run_regression() -> int:
    root = Path(__file__).resolve().parents[2]
    patterns = [
        "tests/test_cli.py",
        "tests/test_service.py",
        "tests/test_providers_new.py",
        "tests/test_smoke.py",
        "tests/test_regression.py",
    ]
    cmd = [sys.executable, "-m", "pytest", *patterns]
    return subprocess.call(cmd, cwd=str(root))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="smart-search", description="Smart Search CLI for AI-agent web research.")
    parser.add_argument("-v", "--v", "--version", action="version", version=f"%(prog)s {_get_version()}")
    sub = parser.add_subparsers(dest="command", required=True)

    search_parser = sub.add_parser(
        "search", aliases=COMMAND_ALIASES["search"], help="Run OpenAI-compatible web search."
    )
    search_parser.set_defaults(command="search")
    search_parser.add_argument("query")
    search_parser.add_argument("--platform", default="")
    search_parser.add_argument("--model", default="")
    search_parser.add_argument("--extra-sources", type=int, default=0)
    search_parser.add_argument("--validation", choices=["fast", "balanced", "strict"], default="")
    search_parser.add_argument("--fallback", choices=["auto", "off"], default="")
    search_parser.add_argument("--providers", default="auto")
    search_parser.add_argument("--timeout", type=float, default=90, metavar="SECONDS", help="Hard timeout in seconds.")
    _add_format_args(search_parser)

    fetch_parser = sub.add_parser("fetch", aliases=COMMAND_ALIASES["fetch"], help="Fetch a URL as markdown.")
    fetch_parser.set_defaults(command="fetch")
    fetch_parser.add_argument("url")
    _add_format_args(fetch_parser)

    map_parser = sub.add_parser("map", aliases=COMMAND_ALIASES["map"], help="Map a website structure.")
    map_parser.set_defaults(command="map")
    map_parser.add_argument("url")
    map_parser.add_argument("--instructions", default="")
    map_parser.add_argument("--max-depth", type=int, default=1)
    map_parser.add_argument("--max-breadth", type=int, default=20)
    map_parser.add_argument("--limit", type=int, default=50)
    map_parser.add_argument("--timeout", type=int, default=150)
    _add_format_args(map_parser)

    exa_parser = sub.add_parser(
        "exa-search", aliases=COMMAND_ALIASES["exa-search"], help="Run Exa source-first search."
    )
    exa_parser.set_defaults(command="exa-search")
    exa_parser.add_argument("query")
    exa_parser.add_argument("--num-results", type=int, default=5)
    exa_parser.add_argument("--search-type", choices=["neural", "keyword", "auto"], default="neural")
    exa_parser.add_argument("--include-text", action="store_true")
    exa_parser.add_argument("--include-highlights", action="store_true")
    exa_parser.add_argument("--start-published-date", default="")
    exa_parser.add_argument("--include-domains", default="")
    exa_parser.add_argument("--exclude-domains", default="")
    exa_parser.add_argument("--category", default="")
    _add_format_args(exa_parser)

    similar_parser = sub.add_parser(
        "exa-similar", aliases=COMMAND_ALIASES["exa-similar"], help="Find pages similar to a URL with Exa."
    )
    similar_parser.set_defaults(command="exa-similar")
    similar_parser.add_argument("url")
    similar_parser.add_argument("--num-results", type=int, default=5)
    _add_format_args(similar_parser)

    zhipu_parser = sub.add_parser(
        "zhipu-search", aliases=COMMAND_ALIASES["zhipu-search"], help="Run Zhipu Web Search source-first search."
    )
    zhipu_parser.set_defaults(command="zhipu-search")
    zhipu_parser.add_argument("query")
    zhipu_parser.add_argument("--count", type=int, default=10)
    zhipu_parser.add_argument("--search-engine", default="")
    zhipu_parser.add_argument("--search-recency-filter", default="noLimit")
    zhipu_parser.add_argument("--search-domain-filter", default="")
    zhipu_parser.add_argument("--content-size", choices=["medium", "high"], default="medium")
    _add_format_args(zhipu_parser)

    context7_library_parser = sub.add_parser(
        "context7-library",
        aliases=COMMAND_ALIASES["context7-library"],
        help="Resolve Context7 library candidates.",
    )
    context7_library_parser.set_defaults(command="context7-library")
    context7_library_parser.add_argument("name")
    context7_library_parser.add_argument("query", nargs="?", default="")
    _add_format_args(context7_library_parser)

    context7_docs_parser = sub.add_parser(
        "context7-docs",
        aliases=COMMAND_ALIASES["context7-docs"],
        help="Fetch Context7 docs for a library.",
    )
    context7_docs_parser.set_defaults(command="context7-docs")
    context7_docs_parser.add_argument("library_id")
    context7_docs_parser.add_argument("query")
    _add_format_args(context7_docs_parser)

    smoke_parser = sub.add_parser(
        "smoke", aliases=COMMAND_ALIASES["smoke"], help="Run provider routing and fallback smoke checks."
    )
    smoke_parser.set_defaults(command="smoke")
    smoke_mode = smoke_parser.add_mutually_exclusive_group()
    smoke_mode.add_argument("--mode", choices=["mock", "live"], default=None)
    smoke_mode.add_argument("--mock", dest="mode", action="store_const", const="mock", help="Run offline mock smoke checks.")
    smoke_mode.add_argument("--live", dest="mode", action="store_const", const="live", help="Run live provider smoke checks.")
    smoke_parser.set_defaults(mode="mock")
    _add_format_args(smoke_parser)

    doctor_parser = sub.add_parser(
        "doctor", aliases=COMMAND_ALIASES["doctor"], help="Show masked configuration and connection checks."
    )
    doctor_parser.set_defaults(command="doctor")
    _add_format_args(doctor_parser)

    model_parser = sub.add_parser(
        "model", aliases=COMMAND_ALIASES["model"], help="Read or change the default OpenAI-compatible model."
    )
    model_parser.set_defaults(command="model")
    model_sub = model_parser.add_subparsers(dest="model_command", required=True)
    model_set = model_sub.add_parser("set", aliases=MODEL_COMMAND_ALIASES["set"])
    model_set.set_defaults(model_command="set")
    model_set.add_argument("model")
    _add_format_args(model_set)
    model_current = model_sub.add_parser("current", aliases=MODEL_COMMAND_ALIASES["current"])
    model_current.set_defaults(model_command="current")
    _add_format_args(model_current)

    setup_parser = sub.add_parser(
        "setup", aliases=COMMAND_ALIASES["setup"], help="Interactively save local provider configuration."
    )
    setup_parser.set_defaults(command="setup")
    setup_parser.add_argument("--non-interactive", action="store_true", help="Only save values passed as flags.")
    setup_parser.add_argument("--lang", choices=["zh", "en"], default="", help="Interactive setup language.")
    setup_parser.add_argument("--advanced", action="store_true", help="Show every low-level config key in interactive setup.")
    setup_parser.add_argument("--api-url", default="", help="Save SMART_SEARCH_API_URL.")
    setup_parser.add_argument("--api-key", default="", help="Save SMART_SEARCH_API_KEY.")
    setup_parser.add_argument("--api-mode", default="", help="Save SMART_SEARCH_API_MODE.")
    setup_parser.add_argument("--xai-tools", default="", help="Save SMART_SEARCH_XAI_TOOLS.")
    setup_parser.add_argument("--model", default="", help="Save SMART_SEARCH_MODEL.")
    setup_parser.add_argument("--xai-api-url", default="", help="Save XAI_API_URL.")
    setup_parser.add_argument("--xai-api-key", default="", help="Save XAI_API_KEY.")
    setup_parser.add_argument("--xai-model", default="", help="Save XAI_MODEL.")
    setup_parser.add_argument("--xai-tools-explicit", default="", help="Save XAI_TOOLS.")
    setup_parser.add_argument("--openai-compatible-api-url", default="", help="Save OPENAI_COMPATIBLE_API_URL.")
    setup_parser.add_argument("--openai-compatible-api-key", default="", help="Save OPENAI_COMPATIBLE_API_KEY.")
    setup_parser.add_argument("--openai-compatible-model", default="", help="Save OPENAI_COMPATIBLE_MODEL.")
    setup_parser.add_argument("--validation-level", default="", help="Save SMART_SEARCH_VALIDATION_LEVEL.")
    setup_parser.add_argument("--fallback-mode", default="", help="Save SMART_SEARCH_FALLBACK_MODE.")
    setup_parser.add_argument("--minimum-profile", default="", help="Save SMART_SEARCH_MINIMUM_PROFILE.")
    setup_parser.add_argument("--exa-key", default="", help="Save EXA_API_KEY.")
    setup_parser.add_argument("--context7-key", default="", help="Save CONTEXT7_API_KEY.")
    setup_parser.add_argument("--zhipu-key", default="", help="Save ZHIPU_API_KEY.")
    setup_parser.add_argument("--tavily-key", default="", help="Save TAVILY_API_KEY.")
    setup_parser.add_argument("--firecrawl-key", default="", help="Save FIRECRAWL_API_KEY.")
    _add_format_args(setup_parser)

    config_parser = sub.add_parser(
        "config", aliases=COMMAND_ALIASES["config"], help="Read or edit the local Smart Search config file."
    )
    config_parser.set_defaults(command="config")
    config_sub = config_parser.add_subparsers(dest="config_command", required=True)
    config_path = config_sub.add_parser("path", aliases=CONFIG_COMMAND_ALIASES["path"])
    config_path.set_defaults(config_command="path")
    _add_format_args(config_path)
    config_list = config_sub.add_parser("list", aliases=CONFIG_COMMAND_ALIASES["list"])
    config_list.set_defaults(config_command="list")
    _add_format_args(config_list)
    config_set = config_sub.add_parser("set", aliases=CONFIG_COMMAND_ALIASES["set"])
    config_set.set_defaults(config_command="set")
    config_set.add_argument("key")
    config_set.add_argument("value")
    _add_format_args(config_set)
    config_unset = config_sub.add_parser("unset", aliases=CONFIG_COMMAND_ALIASES["unset"])
    config_unset.set_defaults(config_command="unset")
    config_unset.add_argument("key")
    _add_format_args(config_unset)

    regression_parser = sub.add_parser(
        "regression", aliases=COMMAND_ALIASES["regression"], help="Run offline CLI regression tests."
    )
    regression_parser.set_defaults(command="regression")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "regression":
            return _run_regression()
        if args.command == "setup":
            return _run_setup(args)
        if args.command == "config":
            return _run_config(args)
        if args.command == "model":
            return _run_model(args)
        return asyncio.run(_run_async(args))
    except KeyboardInterrupt:
        return EXIT_RUNTIME_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
