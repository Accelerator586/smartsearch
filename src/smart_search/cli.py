import argparse
import asyncio
import json
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


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


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
        "timeout_seconds": timeout,
    }


def _format_markdown(command: str, data: dict[str, Any]) -> str:
    if command == "search":
        lines = [data.get("content", "")]
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
    return EXIT_RUNTIME_ERROR


def _print_result(command: str, data: dict[str, Any], fmt: str, output: str = "") -> int:
    rendered = _render(command, data, fmt)
    if output:
        service.write_output(output, rendered)
    sys.stdout.write(rendered)
    if rendered and not rendered.endswith("\n"):
        sys.stdout.write("\n")
    return _exit_code(data)


def _add_format_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--output", default="", help="Write rendered output to a file.")


async def _run_async(args: argparse.Namespace) -> int:
    if args.command == "search":
        try:
            data = await asyncio.wait_for(
                service.search(args.query, platform=args.platform, model=args.model, extra_sources=args.extra_sources),
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


def _run_regression() -> int:
    root = Path(__file__).resolve().parents[2]
    patterns = [
        "tests/test_cli.py",
        "tests/test_service.py",
        "tests/test_regression.py",
    ]
    cmd = [sys.executable, "-m", "pytest", *patterns]
    return subprocess.call(cmd, cwd=str(root))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="smart-search", description="Smart Search CLI for AI-agent web research.")
    sub = parser.add_subparsers(dest="command", required=True)

    search_parser = sub.add_parser("search", help="Run OpenAI-compatible web search.")
    search_parser.add_argument("query")
    search_parser.add_argument("--platform", default="")
    search_parser.add_argument("--model", default="")
    search_parser.add_argument("--extra-sources", type=int, default=0)
    search_parser.add_argument("--timeout", type=float, default=90, metavar="SECONDS", help="Hard timeout in seconds.")
    _add_format_args(search_parser)

    fetch_parser = sub.add_parser("fetch", help="Fetch a URL as markdown.")
    fetch_parser.add_argument("url")
    _add_format_args(fetch_parser)

    map_parser = sub.add_parser("map", help="Map a website structure.")
    map_parser.add_argument("url")
    map_parser.add_argument("--instructions", default="")
    map_parser.add_argument("--max-depth", type=int, default=1)
    map_parser.add_argument("--max-breadth", type=int, default=20)
    map_parser.add_argument("--limit", type=int, default=50)
    map_parser.add_argument("--timeout", type=int, default=150)
    _add_format_args(map_parser)

    exa_parser = sub.add_parser("exa-search", help="Run Exa source-first search.")
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

    similar_parser = sub.add_parser("exa-similar", help="Find pages similar to a URL with Exa.")
    similar_parser.add_argument("url")
    similar_parser.add_argument("--num-results", type=int, default=5)
    _add_format_args(similar_parser)

    doctor_parser = sub.add_parser("doctor", help="Show masked configuration and connection checks.")
    _add_format_args(doctor_parser)

    model_parser = sub.add_parser("model", help="Read or change the default OpenAI-compatible model.")
    model_sub = model_parser.add_subparsers(dest="model_command", required=True)
    model_set = model_sub.add_parser("set")
    model_set.add_argument("model")
    _add_format_args(model_set)
    model_current = model_sub.add_parser("current")
    _add_format_args(model_current)

    sub.add_parser("regression", help="Run offline CLI regression tests.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "regression":
            return _run_regression()
        if args.command == "model":
            return _run_model(args)
        return asyncio.run(_run_async(args))
    except KeyboardInterrupt:
        return EXIT_RUNTIME_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
