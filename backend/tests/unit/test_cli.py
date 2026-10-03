"""Tests for MCP Forge CLI."""

from typer.testing import CliRunner

from mcp_forge.cli.main import app
from mcp_forge.version import __version__

runner = CliRunner()


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "MCP Forge" in result.output
    assert "generate" in result.output


def test_cli_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output
