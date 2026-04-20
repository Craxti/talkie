"""Integration-style tests: CLI behavior aligned with README (local HTTP only)."""

from __future__ import annotations

import json
from unittest.mock import patch
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from talkie.cli.main import app
from talkie.utils.history import reset_history_manager

pytest_httpserver = pytest.importorskip("pytest_httpserver")
HTTPServer = pytest_httpserver.HTTPServer


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def talkie_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TALKIE_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("TALKIE_HISTORY_FILE", str(tmp_path / "history.json"))
    reset_history_manager()
    yield
    reset_history_manager()


@pytest.fixture
def http_srv() -> HTTPServer:
    srv = HTTPServer()
    srv.start()
    yield srv
    srv.stop()


def test_readme_get_json(runner: CliRunner, talkie_env: None, http_srv: HTTPServer) -> None:
    http_srv.expect_request("/users", method="GET").respond_with_json({"items": []})
    url = http_srv.url_for("/users")
    result = runner.invoke(app, ["get", url, "--json"])
    assert result.exit_code == 0, result.stdout
    # Rich may write to stderr; Click merges stderr into stdout by default.
    out = result.stdout
    assert "items" in out


def test_readme_post_positional_and_history(
    runner: CliRunner, talkie_env: None, http_srv: HTTPServer
) -> None:
    http_srv.expect_request("/create", method="POST").respond_with_json({"ok": True})
    url = http_srv.url_for("/create")
    result = runner.invoke(app, ["post", url, "name=Ann", "n:=1"])
    assert result.exit_code == 0, result.stdout

    h = runner.invoke(app, ["history", "list", "--limit", "5"])
    hout = h.stdout
    assert h.exit_code == 0
    assert http_srv.host in hout or "/create" in hout


def test_readme_post_form_flags(
    runner: CliRunner, talkie_env: None, http_srv: HTTPServer
) -> None:
    http_srv.expect_request("/x", method="POST").respond_with_json({"id": 2})
    url = http_srv.url_for("/x")
    r = runner.invoke(app, ["post", url, "-F", "id:=2"])
    assert r.exit_code == 0


def test_readme_parallel_file(
    runner: CliRunner, talkie_env: None, http_srv: HTTPServer, tmp_path: Path
) -> None:
    http_srv.expect_request("/a", method="GET").respond_with_data("A")
    http_srv.expect_request("/b", method="GET").respond_with_data("B")
    http_srv.expect_request("/p", method="POST").respond_with_json({"done": True})

    f = tmp_path / "req.txt"
    f.write_text(
        "\n".join(
            [
                f"GET {http_srv.url_for('/a')}",
                f"GET {http_srv.url_for('/b')}",
                f"POST {http_srv.url_for('/p')} -F name=Z",
            ]
        ),
        encoding="utf-8",
    )

    r = runner.invoke(app, ["parallel", "-f", str(f), "--concurrency", "2"])
    rout = r.stdout
    assert r.exit_code == 0, rout
    assert "200" in rout


def test_readme_curl_generate(runner: CliRunner, talkie_env: None) -> None:
    r = runner.invoke(
        app,
        [
            "curl",
            "https://example.com/api",
            "-H",
            "Authorization: Bearer x",
            "-q",
            "page=1",
        ],
    )
    assert r.exit_code == 0
    out = r.stdout
    assert "curl" in out
    assert "example.com" in out


def test_readme_format_json(tmp_path: Path, runner: CliRunner) -> None:
    p = tmp_path / "t.json"
    p.write_text('{"z":1,"a":2}', encoding="utf-8")
    r = runner.invoke(app, ["format", str(p)])
    out = r.stdout
    assert r.exit_code == 0
    assert "z" in out


def test_readme_openapi_local_file(tmp_path: Path, runner: CliRunner) -> None:
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Demo", "version": "1.0"},
        "paths": {"/hello": {"get": {"summary": "Say hi"}}},
    }
    p = tmp_path / "api.yaml"
    p.write_text(yaml.dump(spec), encoding="utf-8")
    r = runner.invoke(app, ["openapi", str(p), "--endpoints"])
    out = r.stdout
    assert r.exit_code == 0
    assert "/hello" in out


def test_readme_graphql_local(
    runner: CliRunner, talkie_env: None, http_srv: HTTPServer
) -> None:
    http_srv.expect_request("/graphql", method="POST").respond_with_json(
        {"data": {"hello": "world"}}
    )
    url = http_srv.url_for("/graphql")
    r = runner.invoke(app, ["graphql", url, "-q", "{ hello }"])
    out = r.stdout
    assert r.exit_code == 0
    assert "world" in out


def test_readme_headers_query_and_output_file(
    runner: CliRunner, talkie_env: None, http_srv: HTTPServer, tmp_path: Path
) -> None:
    http_srv.expect_request(
        "/users",
        method="GET",
        query_string="page=1&limit=10",
    ).respond_with_json({"ok": True})
    url = http_srv.url_for("/users")
    out_file = tmp_path / "users.json"
    r = runner.invoke(
        app,
        [
            "get",
            url,
            "-H",
            "Authorization: Bearer token123",
            "-H",
            "Accept: application/json",
            "-q",
            "page=1",
            "-q",
            "limit=10",
            "-o",
            str(out_file),
        ],
    )
    assert r.exit_code == 0, r.stdout
    assert out_file.exists()
    assert "ok" in out_file.read_text(encoding="utf-8")


def test_readme_output_modes_verbose_headers_and_format(
    runner: CliRunner, talkie_env: None, http_srv: HTTPServer
) -> None:
    http_srv.expect_request("/users", method="GET").respond_with_json({"items": [1]})
    url = http_srv.url_for("/users")
    rv = runner.invoke(app, ["get", url, "-v"])
    assert rv.exit_code == 0, rv.stdout
    assert "Response headers" in rv.stdout

    rh = runner.invoke(app, ["get", url, "--headers"])
    assert rh.exit_code == 0, rh.stdout
    assert "content-type" in rh.stdout.lower()

    http_srv.expect_request("/xml", method="GET").respond_with_data(
        "<root><item>1</item></root>", content_type="application/xml"
    )
    rx = runner.invoke(app, ["get", http_srv.url_for("/xml"), "-f", "xml"])
    assert rx.exit_code == 0, rx.stdout
    assert "root" in rx.stdout.lower()


def test_readme_curl_related_commands(
    runner: CliRunner, talkie_env: None, http_srv: HTTPServer
) -> None:
    http_srv.expect_request("/users", method="GET").respond_with_json({"ok": True})
    url = http_srv.url_for("/users")
    r = runner.invoke(app, ["get", url, "--curl"])
    assert r.exit_code == 0, r.stdout
    assert "curl" in r.stdout

    rc = runner.invoke(app, ["from-curl", f"curl -s {url}"])
    assert rc.exit_code == 0, rc.stdout
    assert "200" in rc.stdout or "ok" in rc.stdout.lower()


def test_readme_demo_command_mocked(runner: CliRunner) -> None:
    fake_result = {
        "status": 200,
        "headers": {"content-type": "application/json"},
        "body": '{"demo": true}',
        "elapsed_seconds": 0.01,
        "url": "https://httpbin.org/get?talkie=demo",
        "method": "GET",
        "request_headers": {"User-Agent": "Talkie/test"},
    }
    with patch("talkie.cli.main.execute_request", return_value=fake_result):
        r = runner.invoke(app, ["demo"])
    assert r.exit_code == 0, r.stdout
    assert "Talkie demo" in r.stdout


def test_readme_openapi_examples(
    tmp_path: Path, runner: CliRunner
) -> None:
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Demo", "version": "1.0"},
        "servers": [{"url": "https://api.example.com"}],
        "paths": {
            "/users": {
                "get": {"summary": "List users"},
                "post": {"summary": "Create user"},
            }
        },
    }
    p = tmp_path / "api.yaml"
    p.write_text(yaml.dump(spec), encoding="utf-8")
    r = runner.invoke(app, ["openapi", str(p), "--examples"])
    assert r.exit_code == 0, r.stdout
    assert "https://api.example.com/users" in r.stdout


def test_readme_graphql_file_and_variables(
    runner: CliRunner, talkie_env: None, http_srv: HTTPServer, tmp_path: Path
) -> None:
    http_srv.expect_request("/graphql", method="POST").respond_with_json(
        {"data": {"user": {"id": 123}}}
    )
    qf = tmp_path / "query.graphql"
    qf.write_text("query($id: Int!) { user(id: $id) { id } }", encoding="utf-8")
    r = runner.invoke(
        app,
        [
            "graphql",
            http_srv.url_for("/graphql"),
            "-f",
            str(qf),
            "-v",
            "id=123",
        ],
    )
    assert r.exit_code == 0, r.stdout
    assert "123" in r.stdout


def test_readme_history_search_export_import_clear_and_repeat(
    runner: CliRunner, talkie_env: None, http_srv: HTTPServer, tmp_path: Path
) -> None:
    http_srv.expect_request("/users", method="GET").respond_with_json({"a": 1})
    http_srv.expect_request("/users/1", method="GET").respond_with_data("u1")
    u1 = http_srv.url_for("/users")
    u2 = http_srv.url_for("/users/1")
    assert runner.invoke(app, ["get", u1]).exit_code == 0
    assert runner.invoke(app, ["get", u2]).exit_code == 0

    s = runner.invoke(app, ["history", "search", "--method", "GET", "--url", "users"])
    assert s.exit_code == 0, s.stdout
    assert "users" in s.stdout

    a = runner.invoke(
        app,
        [
            "history",
            "search",
            "--domain",
            http_srv.host,
            "--status-min",
            "200",
            "--status-max",
            "299",
            "--sort",
            "desc",
        ],
    )
    assert a.exit_code == 0, a.stdout

    efile = tmp_path / "history.json"
    ex = runner.invoke(app, ["history", "export", str(efile)])
    assert ex.exit_code == 0, ex.stdout
    assert efile.exists()

    lc = runner.invoke(app, ["history", "clear", "--yes"])
    assert lc.exit_code == 0, lc.stdout

    im = runner.invoke(app, ["history", "import", str(efile)])
    assert im.exit_code == 0, im.stdout
    assert "Imported" in im.stdout

    seeded = [
        {
            "id": "12345678-aaaa-bbbb-cccc-1234567890ab",
            "timestamp": "2026-01-01T00:00:00",
            "method": "GET",
            "url": u1,
            "headers": {},
            "data": None,
            "response_status": 200,
            "response_time": 0.01,
        }
    ]
    seed_file = tmp_path / "seed-history.json"
    seed_file.write_text(json.dumps(seeded), encoding="utf-8")
    sim = runner.invoke(app, ["history", "import", str(seed_file)])
    assert sim.exit_code == 0, sim.stdout

    rep = runner.invoke(app, ["history", "repeat", "12345678"])
    assert rep.exit_code == 0, rep.stdout


def test_readme_parallel_output_dir_and_base_urls(
    runner: CliRunner, talkie_env: None, http_srv: HTTPServer, tmp_path: Path
) -> None:
    http_srv.expect_request("/users/1", method="GET").respond_with_data("u1")
    http_srv.expect_request("/users/2", method="GET").respond_with_data("u2")
    out_dir = tmp_path / "results"
    r = runner.invoke(
        app,
        [
            "parallel",
            "-X",
            "GET",
            "-u",
            "/users/1",
            "-u",
            "/users/2",
            "-b",
            http_srv.url_for(""),
            "--output-dir",
            str(out_dir),
        ],
    )
    assert r.exit_code == 0, r.stdout
    files = list(out_dir.glob("resp_*.txt"))
    assert files
