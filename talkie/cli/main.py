"""Typer CLI for Talkie: HTTP, history, OpenAPI, GraphQL, demo, curl import."""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from talkie.__version__ import __version__
from talkie.cli.curl_parser import parse_curl_command
from talkie.cli.execute import execute_request, parse_httpie_items
from talkie.cli.parallel_parse import ParallelJob, parse_parallel_line
from talkie.utils.config import load_config
from talkie.utils.curl_generator import generate_curl_command
from talkie.utils.formatter import DataFormatter, detect_content_type
from talkie.utils.graphql import GraphQLClient
from talkie.utils.history import get_history_manager
from talkie.utils.openapi import OpenAPIClient, validate_openapi_spec

app = typer.Typer(
    name="talkie",
    help=(
        "Talkie — HTTP in the terminal. "
        "[dim]Examples:[/dim] [cyan]talkie get https://httpbin.org/get[/cyan] · "
        "[cyan]talkie demo[/cyan] · [cyan]talkie history list[/cyan]"
    ),
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console(stderr=True)

EXAMPLES = r"""
[bold]Examples[/bold]
  talkie get https://httpbin.org/get -v
  talkie post https://httpbin.org/post name=Talkie version:=0.2
  talkie history list --limit 5
  talkie from-curl 'curl -s https://httpbin.org/get'
  talkie openapi https://petstore3.swagger.io/api/v3/openapi.json --endpoints
  talkie demo
  http GET https://httpbin.org/get   [dim](via `http` script, HTTPie-style)[/dim]
"""


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Print version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Talkie CLI."""
    if ctx.invoked_subcommand is None:
        console.print(Panel.fit(f"Talkie {__version__}\nRun [cyan]talkie --help[/cyan] for commands."))
        console.print(Markdown(EXAMPLES))


def _human_http_error(exc: BaseException) -> None:
    if isinstance(exc, httpx.TimeoutException):
        console.print("[red]Request timed out.[/red] Try a larger [cyan]--timeout[/cyan].")
    elif isinstance(exc, httpx.ConnectError):
        console.print(f"[red]Could not connect:[/red] {exc}")
    elif isinstance(exc, httpx.HTTPStatusError):
        console.print(f"[red]HTTP {exc.response.status_code}[/red] {exc.request.url}")
    else:
        console.print(f"[red]{type(exc).__name__}:[/red] {exc}")


def _print_response(
    result: Dict[str, Any],
    *,
    verbose: bool,
    json_only: bool,
    headers_only: bool,
    output_format: Optional[str],
    show_curl: bool,
    method: str,
    query_list: List[str],
) -> None:
    if show_curl:
        qh: Dict[str, str] = {}
        for q in query_list:
            if "=" in q:
                k, v = q.split("=", 1)
                qh[k.strip()] = v.strip()
        req_h = result.get("request_headers") or {}
        curl = generate_curl_command(
            method,
            result["url"],
            headers=req_h,
            params=qh or None,
        )
        console.print(Panel(curl, title="curl", border_style="dim"))

    if verbose:
        console.print(
            f"[dim]{result['method']}[/dim] {result['url']} "
            f"[dim]→ {result['status']} in {result.get('elapsed_seconds', 0):.3f}s[/dim]"
        )

    if headers_only or verbose:
        tbl = Table(title="Response headers" if verbose else None, show_header=True)
        tbl.add_column("Name")
        tbl.add_column("Value")
        for k, v in result["headers"].items():
            tbl.add_row(k, v[:200] + ("…" if len(v) > 200 else ""))
        console.print(tbl)

    if headers_only:
        return

    body = result.get("body") or ""
    if json_only:
        try:
            parsed = json.loads(body)
            console.print(
                Syntax(
                    json.dumps(parsed, indent=2, ensure_ascii=False),
                    "json",
                    theme="monokai",
                    word_wrap=True,
                )
            )
        except json.JSONDecodeError:
            console.print(body)
        return

    fmt = DataFormatter(console=Console())
    ct = output_format or result["headers"].get("content-type", "").split(";")[0].strip()
    if not ct:
        ct = detect_content_type(body)
        mime = {
            "json": "application/json",
            "xml": "application/xml",
            "html": "text/html",
            "text": "text/plain",
        }.get(ct, "text/plain")
    else:
        mime = ct

    if output_format:
        text = fmt.format_data(body, mime, format_type=output_format)
        console.print(text)
    else:
        fmt.display_formatted(body, mime or "text/plain")


def _run_http(
    method: str,
    url: str,
    headers: List[str],
    query: List[str],
    body_items: List[str],
    raw_body: Optional[str],
    json_body: Optional[str],
    verbose: bool,
    json_only: bool,
    headers_only: bool,
    output_format: Optional[str],
    show_curl: bool,
    output_path: Optional[Path],
    timeout: float,
    insecure: bool,
) -> None:
    cfg = load_config()

    jb: Any = None
    if json_body is not None:
        jb = json.loads(json_body)
    elif body_items:
        jb = parse_httpie_items(body_items)

    try:
        result = execute_request(
            method,
            url,
            config=cfg,
            header_pairs=headers,
            query_pairs=query,
            json_body=jb,
            raw_body=raw_body,
            timeout=timeout,
            verify=not insecure,
        )
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(2) from exc
    except httpx.HTTPError as exc:
        _human_http_error(exc)
        raise typer.Exit(1) from exc

    _print_response(
        result,
        verbose=verbose,
        json_only=json_only,
        headers_only=headers_only,
        output_format=output_format,
        show_curl=show_curl,
        method=method,
        query_list=query,
    )

    if output_path:
        output_path.write_text(result.get("body") or "", encoding="utf-8")
        console.print(f"[green]Wrote[/green] {output_path}")


@app.command("demo")
def demo_cmd() -> None:
    """Three quick wins: GET + JSON + curl + history hint (needs network)."""
    console.print(
        Panel.fit(
            "[bold]Talkie demo[/bold]\n"
            "1) GET https://httpbin.org/get\n"
            "2) Pretty JSON + curl preview\n"
            "3) Saved to [cyan]talkie history[/cyan]",
            border_style="cyan",
        )
    )
    try:
        result = execute_request(
            "GET",
            "https://httpbin.org/get",
            query_pairs=["talkie=demo"],
            timeout=15.0,
        )
    except Exception as exc:
        console.print(f"[yellow]Demo request skipped (offline?):[/yellow] {exc}")
        console.print(Markdown("Try: `talkie get https://httpbin.org/get` when online."))
        raise typer.Exit(0) from exc

    _print_response(
        result,
        verbose=True,
        json_only=False,
        headers_only=False,
        output_format=None,
        show_curl=True,
        method="GET",
        query_list=["talkie=demo"],
    )
    console.print("\n[dim]Next:[/dim] [cyan]talkie history list --limit 3[/cyan]")


@app.command("from-curl")
def from_curl_cmd(
    curl: str = typer.Argument(..., help="Full curl command in quotes."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show parsed request only."),
) -> None:
    """Replay a curl one-liner as an HTTP request."""
    try:
        parsed = parse_curl_command(curl)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(2) from exc

    if dry_run:
        console.print_json(data=parsed)
        return

    hdrs = [f"{k}: {v}" for k, v in parsed["headers"].items()]
    method = parsed["method"]
    url = parsed["url"]
    jb = parsed.get("data")
    raw = None
    if isinstance(jb, (dict, list)):
        body_items: List[str] = []
        json_str = json.dumps(jb)
        _run_http(
            method,
            url,
            hdrs,
            [],
            body_items,
            raw_body=None,
            json_body=json_str,
            verbose=True,
            json_only=False,
            headers_only=False,
            output_format=None,
            show_curl=False,
            output_path=None,
            timeout=30.0,
            insecure=bool(parsed.get("insecure")),
        )
    elif jb is not None:
        _run_http(
            method,
            url,
            hdrs,
            [],
            [],
            raw_body=str(jb),
            json_body=None,
            verbose=True,
            json_only=False,
            headers_only=False,
            output_format=None,
            show_curl=False,
            output_path=None,
            timeout=30.0,
            insecure=bool(parsed.get("insecure")),
        )
    else:
        _run_http(
            method,
            url,
            hdrs,
            [],
            [],
            raw_body=None,
            json_body=None,
            verbose=True,
            json_only=False,
            headers_only=False,
            output_format=None,
            show_curl=False,
            output_path=None,
            timeout=30.0,
            insecure=bool(parsed.get("insecure")),
        )


@app.command("curl")
def curl_only_cmd(
    url: str = typer.Argument(...),
    method: str = typer.Option("GET", "-X", "--request"),
    header: List[str] = typer.Option([], "-H", "--header", help='Header "Name: value".'),
    query: List[str] = typer.Option([], "-q", "--query", help="Query key=value."),
) -> None:
    """Print an equivalent curl command (no network)."""
    cfg = load_config()
    from talkie.cli.execute import merge_headers, parse_header_pairs, parse_query_pairs, resolve_url

    full = resolve_url(url, cfg)
    merged = merge_headers(cfg, parse_header_pairs(header))
    qh = parse_query_pairs(query)
    line = generate_curl_command(method.upper(), full, headers=merged, params=qh or None)
    console.print(line)


def _register_http_method(method: str, *, allow_positional_body: bool) -> None:
    """Register one Typer command per HTTP verb."""

    if allow_positional_body:

        def command_fn(
            url: str = typer.Argument(..., help="URL or path when base_url is set."),
            positional: Optional[List[str]] = typer.Argument(
                None,
                help="Optional key=value or key:=json after URL (httpie-style, with -F).",
            ),
            header: List[str] = typer.Option(
                [], "-H", "--header", help='Header "Name: value".'
            ),
            query: List[str] = typer.Option([], "-q", "--query", help="Query key=value."),
            form: List[str] = typer.Option(
                [],
                "-F",
                "--form",
                help="Body field key=value or key:=json (repeatable).",
            ),
            data_raw: Optional[str] = typer.Option(
                None, "--data", "-d", help="Raw request body string."
            ),
            data_json: Optional[str] = typer.Option(
                None, "--data-json", help="Request body as JSON string."
            ),
            verbose: bool = typer.Option(False, "-v", "--verbose"),
            json_out: bool = typer.Option(
                False, "--json", help="Print response body as formatted JSON only."
            ),
            headers_only: bool = typer.Option(
                False, "--headers", help="Print response headers only."
            ),
            output_format: Optional[str] = typer.Option(
                None, "-f", "--format", help="json|xml|html"
            ),
            show_curl: bool = typer.Option(
                False, "--curl", help="Also print curl equivalent."
            ),
            output_path: Optional[Path] = typer.Option(
                None, "-o", "--output", help="Save response body to file."
            ),
            timeout: float = typer.Option(30.0, "--timeout"),
            insecure: bool = typer.Option(
                False, "-k", "--insecure", help="Disable TLS certificate verification."
            ),
        ) -> None:
            body_list = list(positional or []) + list(form)
            _run_http(
                method,
                url,
                header,
                query,
                body_list,
                data_raw,
                data_json,
                verbose,
                json_out,
                headers_only,
                output_format,
                show_curl,
                output_path,
                timeout,
                insecure,
            )

    else:

        def command_fn(
            url: str = typer.Argument(..., help="URL or path when base_url is set."),
            header: List[str] = typer.Option(
                [], "-H", "--header", help='Header "Name: value".'
            ),
            query: List[str] = typer.Option([], "-q", "--query", help="Query key=value."),
            data_raw: Optional[str] = typer.Option(
                None, "--data", "-d", help="Raw request body string."
            ),
            data_json: Optional[str] = typer.Option(
                None, "--data-json", help="Request body as JSON string."
            ),
            verbose: bool = typer.Option(False, "-v", "--verbose"),
            json_out: bool = typer.Option(
                False, "--json", help="Print response body as formatted JSON only."
            ),
            headers_only: bool = typer.Option(
                False, "--headers", help="Print response headers only."
            ),
            output_format: Optional[str] = typer.Option(
                None, "-f", "--format", help="json|xml|html"
            ),
            show_curl: bool = typer.Option(
                False, "--curl", help="Also print curl equivalent."
            ),
            output_path: Optional[Path] = typer.Option(
                None, "-o", "--output", help="Save response body to file."
            ),
            timeout: float = typer.Option(30.0, "--timeout"),
            insecure: bool = typer.Option(
                False, "-k", "--insecure", help="Disable TLS certificate verification."
            ),
        ) -> None:
            body_list: List[str] = []
            _run_http(
                method,
                url,
                header,
                query,
                body_list,
                data_raw,
                data_json,
                verbose,
                json_out,
                headers_only,
                output_format,
                show_curl,
                output_path,
                timeout,
                insecure,
            )

    command_fn.__name__ = f"cmd_{method.lower()}"
    app.command(method.lower(), help=f"{method} request.")(command_fn)


for _verb in ("GET", "DELETE", "HEAD", "OPTIONS"):
    _register_http_method(_verb, allow_positional_body=False)

for _verb in ("POST", "PUT", "PATCH"):
    _register_http_method(_verb, allow_positional_body=True)


history_app = typer.Typer(help="List, search, repeat, import/export request history.")
app.add_typer(history_app, name="history")


@history_app.command("list")
def history_list(
    limit: int = typer.Option(20, "--limit", "-n", help="Last N entries."),
) -> None:
    mgr = get_history_manager()
    rows = mgr.get_history(limit=limit)
    tbl = Table(title=f"History (last {len(rows)})")
    tbl.add_column("id", style="cyan", no_wrap=True, max_width=10)
    tbl.add_column("time")
    tbl.add_column("M", width=4)
    tbl.add_column("status", width=6)
    tbl.add_column("url")
    for e in rows:
        tbl.add_row(
            str(e.get("id", ""))[:8] + "…",
            str(e.get("timestamp", ""))[:19],
            str(e.get("method", "")),
            str(e.get("response_status", "")),
            str(e.get("url", ""))[:80],
        )
    console.print(tbl)


@history_app.command("search")
def history_search(
    method: Optional[str] = typer.Option(None, "--method"),
    url: Optional[str] = typer.Option(None, "--url"),
    status: Optional[int] = typer.Option(None, "--status"),
    since: Optional[str] = typer.Option(None, "--since", help="ISO timestamp lower bound."),
    until: Optional[str] = typer.Option(None, "--until"),
    status_min: Optional[int] = typer.Option(None, "--status-min"),
    status_max: Optional[int] = typer.Option(None, "--status-max"),
    domain: Optional[str] = typer.Option(None, "--domain", help="Host substring."),
    sort: str = typer.Option("asc", "--sort", help="asc|desc by timestamp."),
) -> None:
    mgr = get_history_manager()
    order = "desc" if sort.lower() == "desc" else "asc"
    found = mgr.search_history(
        method=method,
        url_pattern=url,
        status_code=status,
        since=since,
        until=until,
        status_min=status_min,
        status_max=status_max,
        domain=domain,
        sort=order,
    )
    console.print(f"[dim]{len(found)} match(es)[/dim]")
    for e in found[-50:]:
        console.print(
            f"[cyan]{e.get('id', '')[:8]}[/cyan] {e.get('timestamp')} "
            f"{e.get('method')} {e.get('response_status')} {e.get('url')}"
        )


@history_app.command("repeat")
def history_repeat(
    entry_id: str = typer.Argument(..., help="History entry id (prefix from list)."),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    mgr = get_history_manager()
    match = mgr.get_by_id(entry_id)
    if not match and len(entry_id) < 36:
        for e in reversed(mgr.get_history()):
            if str(e.get("id", "")).startswith(entry_id):
                match = e
                break
    if not match:
        console.print("[red]No history entry found.[/red]")
        raise typer.Exit(1)
    if dry_run:
        console.print_json(data=match)
        return
    method = str(match.get("method", "GET"))
    url = str(match.get("url", ""))
    hdrs_dict = match.get("headers") or {}
    hdrs = [f"{k}: {v}" for k, v in hdrs_dict.items() if v != "***"]
    data = match.get("data")
    json_body = json.dumps(data) if isinstance(data, (dict, list)) else None
    raw = None if json_body else (str(data) if data is not None else None)
    _run_http(
        method,
        url,
        hdrs,
        [],
        [],
        raw,
        json_body,
        True,
        False,
        False,
        None,
        False,
        None,
        30.0,
        False,
    )


@history_app.command("export")
def history_export(
    path: Path = typer.Argument(...),
    fmt: str = typer.Option("json", "--format", help="json|csv"),
) -> None:
    get_history_manager().export_history(str(path), export_format=fmt)
    console.print(f"[green]Exported[/green] → {path}")


@history_app.command("import")
def history_import_cmd(path: Path = typer.Argument(...)) -> None:
    n = get_history_manager().import_history(str(path))
    console.print(f"[green]Imported[/green] {n} entries")


@history_app.command("clear")
def history_clear(force: bool = typer.Option(False, "--yes", "-y")) -> None:
    if not force:
        console.print("Add [cyan]--yes[/cyan] to confirm.")
        raise typer.Exit(1)
    get_history_manager().clear_history()
    console.print("[green]History cleared.[/green]")


@app.command("openapi")
def openapi_cmd(
    source: str = typer.Argument(..., help="URL or path to OpenAPI JSON/YAML."),
    endpoints_only: bool = typer.Option(False, "--endpoints", help="List paths only."),
    examples: bool = typer.Option(False, "--examples", help="Show sample operations."),
) -> None:
    """Quick inspect: load spec, validate basics, list operations."""
    try:
        client = OpenAPIClient(source)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(2) from exc

    spec = client.spec
    errs = validate_openapi_spec(spec)
    if errs:
        console.print("[yellow]Structure warnings:[/yellow]", ", ".join(errs))

    info = client.get_info()
    console.print(
        Panel.fit(
            f"[bold]{info.get('title', 'API')}[/bold] v{info.get('version', '?')}\n"
            f"[dim]{spec.get('openapi') or spec.get('swagger', 'openapi?')}[/dim]",
            title="OpenAPI",
        )
    )

    if endpoints_only:
        for p in client.get_endpoints():
            methods = ", ".join(client.get_methods_for_path(p))
            console.print(f"[cyan]{p}[/cyan] [dim]{methods}[/dim]")
        return

    if examples:
        for op in client.operations[:15]:
            ex = client.generate_request_example(op["path"], op["method"])
            if ex:
                console.print_json(data=ex)
        if len(client.operations) > 15:
            console.print(f"[dim]… and {len(client.operations) - 15} more[/dim]")
        return

    for op in client.operations[:40]:
        summ = (op.get("operation") or {}).get("summary", "")
        console.print(f"{op['method']:7} {op['path']}  [dim]{summ}[/dim]")
    if len(client.operations) > 40:
        console.print(f"[dim]… {len(client.operations) - 40} more (use --endpoints)[/dim]")


@app.command("graphql")
def graphql_cmd(
    endpoint: str = typer.Argument(...),
    query: Optional[str] = typer.Option(None, "-q", "--query", help="GraphQL query string."),
    query_file: Optional[Path] = typer.Option(
        None, "-f", "--file", help="Query from file."
    ),
    header: List[str] = typer.Option([], "-H", "--header"),
    variable: List[str] = typer.Option([], "-v", "--var", help='Variable name=value (JSON value).'),
) -> None:
    """Run a GraphQL query against an HTTP endpoint."""
    q = query
    if query_file:
        q = query_file.read_text(encoding="utf-8")
    if not q:
        console.print("[red]Provide -q or -f[/red]")
        raise typer.Exit(2)

    variables: Dict[str, Any] = {}
    for raw in variable:
        if "=" not in raw:
            continue
        k, val = raw.split("=", 1)
        k = k.strip()
        val = val.strip()
        try:
            variables[k] = json.loads(val)
        except json.JSONDecodeError:
            variables[k] = val

    hdrs = {}
    for h in header:
        if ":" in h:
            a, b = h.split(":", 1)
            hdrs[a.strip()] = b.strip()

    client = GraphQLClient(endpoint, hdrs)
    try:
        resp = client.query(q, variables or None)
    except httpx.HTTPError as exc:
        _human_http_error(exc)
        raise typer.Exit(1) from exc

    if resp.errors:
        console.print_json(data={"errors": resp.errors})
    if resp.data is not None:
        console.print(
            Syntax(
                json.dumps(resp.data, indent=2, ensure_ascii=False),
                "json",
                theme="monokai",
                word_wrap=True,
            )
        )


@app.command("format")
def format_cmd(
    path: Path = typer.Argument(...),
    type_override: Optional[str] = typer.Option(None, "-t", "--type", help="json|xml|html"),
    out: Optional[Path] = typer.Option(None, "-o", "--output"),
) -> None:
    """Format JSON/XML/HTML file."""
    text = path.read_text(encoding="utf-8")
    fmt = DataFormatter(console=Console())
    ct = type_override or detect_content_type(text)
    mime = {
        "json": "application/json",
        "xml": "application/xml",
        "html": "text/html",
    }.get(ct, "text/plain")
    rendered = fmt.format_data(text, mime, format_type=type_override)
    if out:
        out.write_text(rendered, encoding="utf-8")
    else:
        console.print(rendered)


@app.command("parallel")
def parallel_cmd(
    file: Optional[Path] = typer.Option(None, "-f", "--file", help="One request per line."),
    method: str = typer.Option("GET", "-X", "--method"),
    urls: List[str] = typer.Option([], "-u", "--url", help="URL path or full URL."),
    base: Optional[str] = typer.Option(None, "-b", "--base", help="Base URL for relative -u paths."),
    concurrency: int = typer.Option(5, "--concurrency"),
    delay: float = typer.Option(0.0, "--delay"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir"),
) -> None:
    """Run many HTTP requests concurrently (GET/POST/…; file lines per README)."""
    lines: List[str] = []
    if file:
        lines = [
            ln.strip()
            for ln in file.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.strip().startswith("#")
        ]
    jobs: List[ParallelJob] = []
    for ln in lines:
        try:
            jobs.append(parse_parallel_line(ln))
        except ValueError as exc:
            console.print(f"[red]Bad line[/red] {ln!r}: {exc}")
            raise typer.Exit(2) from exc

    base_url = (base or "").rstrip("/")
    for u in urls:
        if u.startswith("http://") or u.startswith("https://"):
            jobs.append(ParallelJob(method=method.upper(), url=u))
        elif base_url:
            path = u if u.startswith("/") else f"/{u}"
            jobs.append(ParallelJob(method=method.upper(), url=f"{base_url}{path}"))
        else:
            jobs.append(ParallelJob(method=method.upper(), url=u))

    if not jobs:
        console.print("[red]No requests. Use -f or -u.[/red]")
        raise typer.Exit(2)

    cfg = load_config()
    from talkie.cli.execute import resolve_url

    async def run_all() -> List[Dict[str, Any]]:
        sem = asyncio.Semaphore(concurrency)

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:

            async def one(job: ParallelJob) -> Dict[str, Any]:
                async with sem:
                    if delay:
                        await asyncio.sleep(delay)
                    u = job.url
                    url = resolve_url(u, cfg) if not (
                        u.startswith("http://") or u.startswith("https://")
                    ) else u
                    req_kw: Dict[str, Any] = {}
                    if job.method in ("POST", "PUT", "PATCH") and job.json_body is not None:
                        req_kw["json"] = job.json_body
                    t0 = time.perf_counter()
                    r = await client.request(job.method, url, **req_kw)
                    dt = time.perf_counter() - t0
                    return {
                        "method": job.method,
                        "url": url,
                        "status": r.status_code,
                        "body": r.text,
                        "elapsed": dt,
                    }

            return await asyncio.gather(*[one(j) for j in jobs])

    results = asyncio.run(run_all())
    for i, res in enumerate(results):
        console.print(f"[cyan]{res['status']}[/cyan] {res['elapsed']:.3f}s {res['url']}")
        if output_dir:
            p = output_dir / f"resp_{i}.txt"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(res["body"], encoding="utf-8")


@app.command("ws")
def ws_cmd(
    url: str = typer.Argument(...),
    send: Optional[str] = typer.Option(None, "--send", help="Send one message and print reply."),
    header: List[str] = typer.Option([], "-H", "--header"),
) -> None:
    """Minimal WebSocket client (async)."""
    try:
        import websockets
    except ImportError as exc:
        console.print("[red]websockets package required[/red]")
        raise typer.Exit(1) from exc

    extra: List[tuple[str, str]] = []
    for h in header:
        if ":" in h:
            k, v = h.split(":", 1)
            extra.append((k.strip(), v.strip()))

    async def run() -> None:
        async with websockets.connect(url, extra_headers=extra) as ws:
            if send:
                await ws.send(send)
                msg = await asyncio.wait_for(ws.recv(), timeout=15.0)
                console.print(str(msg))
            else:
                console.print("[dim]Connected. Receiving one message (15s timeout)…[/dim]")
                msg = await asyncio.wait_for(ws.recv(), timeout=15.0)
                console.print(str(msg))

    try:
        asyncio.run(run())
    except Exception as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc


@app.command("completion")
def completion_cmd() -> None:
    """How to enable shell tab completion for Talkie (Typer/Click)."""
    console.print(
        Panel(
            "[bold]Shell completion[/bold]\n\n"
            "Typer adds hidden Click options. After install, run:\n"
            "  [cyan]talkie --install-completion bash[/cyan]\n"
            "  [cyan]talkie --install-completion zsh[/cyan]\n"
            "Then restart your shell.\n\n"
            "Or add to [dim]~/.bashrc[/dim] manually (bash example):\n"
            "  [dim]eval \"$(_TYPER_COMPLETE=bash_source talkie)\"[/dim]",
            title="completion",
            border_style="dim",
        )
    )


def main() -> None:
    """Entry point for console_scripts."""
    app()


if __name__ == "__main__":
    main()