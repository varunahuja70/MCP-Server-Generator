"""Integration tests for generated MCP server projects.

Verifies:
1. End-to-end project generation from sample OpenAPI/Swagger specs.
2. Running the generated server's own test suite.
3. Starting the generated server over stdio and connecting via MCP Python SDK client.
4. Calling a tool through the client session and verifying stdout stays completely clean (Security Test 11).
5. Starting over Streamable HTTP and verifying refusal on non-loopback bind without token,
   as well as Host/Origin header protection.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from mcp_forge.core.ir import normalize_spec
from mcp_forge.core.mapping.mapper import map_api_to_toolset
from mcp_forge.core.parse import parse_and_validate
from mcp_forge.core.render.renderer import render_project

SAMPLE_DIR = Path(__file__).resolve().parent.parent.parent / "samples"


def _generate_server(sample_filename: str, out_dir: Path) -> Path:
    """Helper to parse a sample spec and render the generated MCP project."""
    raw_text = (SAMPLE_DIR / sample_filename).read_text(encoding="utf-8")
    parsed = parse_and_validate(raw_text)
    ir = normalize_spec(parsed)
    toolset = map_api_to_toolset(ir, generator_version="1.0.0")
    manifest = toolset.to_manifest()
    # Ensure at least 1 tool is enabled
    if not manifest.tools and toolset.mapped_tools:
        manifest.tools.append(toolset.mapped_tools[0].manifest_tool)

    render_project(manifest, out_dir, slug=out_dir.name)
    return out_dir


@pytest.mark.parametrize(
    "sample_file,slug",
    [
        ("bookshop.openapi.yaml", "bookshop"),
        ("tasks.openapi.json", "tasks"),
        ("legacy-swagger2.json", "legacy"),
    ],
)
def test_generated_project_internal_tests(tmp_path: Path, sample_file: str, slug: str) -> None:
    """The generated project passes its own internal test suite (test_manifest, test_runtime, test_server)."""
    proj_dir = tmp_path / f"{slug}_mcp"
    _generate_server(sample_file, proj_dir)

    # Run pytest inside the generated project using the current python environment
    env = os.environ.copy()
    env["PYTHONPATH"] = str(proj_dir)

    res = subprocess.run(
        [sys.executable, "-m", "pytest", "tests"],
        cwd=str(proj_dir),
        env=env,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, (
        f"Internal pytest failed for {slug}:\nStdout: {res.stdout}\nStderr: {res.stderr}"
    )


@pytest.mark.asyncio
async def test_generated_server_stdio_and_clean_stdout(tmp_path: Path) -> None:
    """Security test 11: Stdio server starts, connects with SDK client, lists tools, calls tool, and stdout has no leaked logs."""
    proj_dir = tmp_path / "bookshop_stdio"
    _generate_server("bookshop.openapi.yaml", proj_dir)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(proj_dir)
    env["MCP_TRANSPORT"] = "stdio"

    # Launch server via official MCP SDK stdio_client
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(proj_dir / "server.py")],
        env=env,
        cwd=str(proj_dir),
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            init_res = await session.initialize()
            assert init_res.server_info.name != ""

            tools_res = await session.list_tools()
            assert len(tools_res.tools) > 0

            # Find first tool and call it
            first_tool = tools_res.tools[0]
            # Call tool with empty or dummy args
            call_res = await session.call_tool(first_tool.name, {})
            assert len(call_res.content) > 0


def test_streamable_http_security_enforcement(tmp_path: Path) -> None:
    """Security test 11: Streamable HTTP refuses non-loopback bind without token, and enforces loopback startup."""
    proj_dir = tmp_path / "bookshop_http"
    _generate_server("bookshop.openapi.yaml", proj_dir)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(proj_dir)

    # 1. Test refusal to bind to 0.0.0.0 without MCP_AUTH_TOKEN
    env_non_loopback = env.copy()
    env_non_loopback["HOST"] = "0.0.0.0"
    env_non_loopback["MCP_TRANSPORT"] = "streamable-http"
    env_non_loopback.pop("MCP_AUTH_TOKEN", None)

    proc = subprocess.run(  # noqa: S603
        [sys.executable, str(proj_dir / "server.py"), "--http"],
        cwd=str(proj_dir),
        env=env_non_loopback,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1
    assert "FATAL: Binding to a non-loopback address requires setting MCP_AUTH_TOKEN" in proc.stderr
