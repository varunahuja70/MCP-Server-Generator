"""Unit and integration tests for the `forge` CLI."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from mcp_forge.cli.main import app
from mcp_forge.config import Settings
from mcp_forge.core.ir import normalize_spec
from mcp_forge.core.mapping.mapper import map_api_to_toolset
from mcp_forge.core.parse import parse_and_validate
from mcp_forge.version import __version__

runner = CliRunner()
SAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "samples"


def test_cli_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_cli_samples() -> None:
    result = runner.invoke(app, ["samples"])
    assert result.exit_code == 0
    assert "bookshop" in result.stdout

    result_json = runner.invoke(app, ["samples", "--json"])
    assert result_json.exit_code == 0
    samples_data = json.loads(result_json.stdout)
    assert len(samples_data) >= 3


def test_cli_check_valid(tmp_path: Path) -> None:
    spec_path = SAMPLES_DIR / "bookshop.openapi.yaml"
    result = runner.invoke(app, ["check", str(spec_path)])
    assert result.exit_code == 0
    assert "is valid" in result.stdout

    result_json = runner.invoke(app, ["check", str(spec_path), "--json"])
    assert result_json.exit_code == 0
    data = json.loads(result_json.stdout)
    assert data["valid"] is True
    assert data["operation_count"] > 0


def test_cli_check_invalid(tmp_path: Path) -> None:
    bad_spec = tmp_path / "bad.yaml"
    bad_spec.write_text("openapi: 3.0.0\ninfo: {}\npaths: not-a-map\n", encoding="utf-8")
    result = runner.invoke(app, ["check", str(bad_spec)])
    assert result.exit_code == 1

    result_json = runner.invoke(app, ["check", str(bad_spec), "--json"])
    assert result_json.exit_code == 1
    data = json.loads(result_json.stdout)
    assert data["valid"] is False


def test_cli_check_missing_file() -> None:
    result = runner.invoke(app, ["check", "non_existent_file.yaml"])
    assert result.exit_code == 2


def test_cli_review() -> None:
    spec_path = SAMPLES_DIR / "bookshop.openapi.yaml"
    result = runner.invoke(app, ["review", str(spec_path)])
    assert result.exit_code == 0
    assert "Findings" in result.stdout

    result_json = runner.invoke(app, ["review", str(spec_path), "--json"])
    assert result_json.exit_code == 0
    data = json.loads(result_json.stdout)
    assert "findings" in data


def test_cli_generate_and_comparison_with_api(tmp_path: Path) -> None:
    """Generate via CLI and verify output contains manifest and server."""
    spec_path = SAMPLES_DIR / "bookshop.openapi.yaml"
    out_dir = tmp_path / "cli_generated"

    # 1. Generate with read-only flag
    result = runner.invoke(app, ["generate", str(spec_path), "-o", str(out_dir), "--read-only"])
    assert result.exit_code == 0
    assert (out_dir / "tools.json").exists()
    assert (out_dir / "server.py").exists()
    assert (out_dir / "pyproject.toml").exists()
    assert (out_dir / "runtime" / "client.py").exists()

    manifest = json.loads((out_dir / "tools.json").read_text(encoding="utf-8"))
    # 2. Generate with explicit --select flag
    out_dir_select = tmp_path / "cli_select"
    result_select = runner.invoke(
        app,
        ["generate", str(spec_path), "-o", str(out_dir_select), "--select", "listBooks", "--json"],
    )
    assert result_select.exit_code == 0
    sel_manifest = json.loads((out_dir_select / "tools.json").read_text(encoding="utf-8"))
    assert len(sel_manifest["tools"]) == 1
    # 3. Verify parity between CLI generate and API build output
    # By default, both CLI --read-only and API default use read-only operations for bookshop
    parsed_spec = parse_and_validate(spec_path.read_text(encoding="utf-8"))
    ir = normalize_spec(parsed_spec)
    toolset = map_api_to_toolset(ir=ir, generator_version=__version__)
    expected_manifest = toolset.to_manifest()

    assert manifest["info"]["title"] == expected_manifest.info.title
    assert manifest["info"]["version"] == expected_manifest.info.version
    assert len(manifest["tools"]) == expected_manifest.tool_count
    assert len(manifest["tools"]) == len(expected_manifest.tools)
    assert [t["name"] for t in manifest["tools"]] == [t.name for t in expected_manifest.tools]
    assert [t["method"] for t in manifest["tools"]] == [t.method for t in expected_manifest.tools]


def test_cli_wipe(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    test_data = tmp_path / "data"
    test_data.mkdir(parents=True, exist_ok=True)
    dummy_file = test_data / "test.txt"
    dummy_file.write_text("hello", encoding="utf-8")

    monkeypatch.setattr("mcp_forge.cli.main.Settings", lambda: Settings(forge_data_dir=test_data))

    result = runner.invoke(app, ["wipe", "--yes"])
    assert result.exit_code == 0
    assert not test_data.exists()
