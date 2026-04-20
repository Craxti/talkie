"""Tests for CLI module."""

from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from talkie.cli.main import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestCliApp:
    """Typer app smoke tests."""

    def test_help(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "get" in result.stdout.lower() or "GET" in result.stdout

    def test_version(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert len(result.stdout.strip()) > 0

    @patch("talkie.cli.main.execute_request")
    def test_get_request(self, mock_exec: Mock, runner: CliRunner) -> None:
        mock_exec.return_value = {
            "status": 200,
            "headers": {"Content-Type": "application/json"},
            "body": '{"result": "success"}',
            "elapsed_seconds": 0.01,
            "url": "https://example.com/",
            "method": "GET",
            "request_headers": {"User-Agent": "test"},
        }

        result = runner.invoke(app, ["get", "https://example.com"])
        assert result.exit_code == 0


class TestCLIImports:
    """Test CLI module imports."""

    def test_cli_imports(self) -> None:
        from talkie.cli import main as cli_main

        assert cli_main is not None

    def test_app_callable(self) -> None:
        assert callable(app)
