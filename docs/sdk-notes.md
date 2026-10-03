# MCP Python SDK v2 Architecture & Integration Notes

This document records verified facts about the official MCP Python SDK v2 (`mcp>=2,<3`, specifically `2.3.0`) targeting protocol specification revision `2026-07-28`.

## 1. Official References & Links
- MCP Specification Revision: `2026-07-28`
  - Specification docs: https://modelcontextprotocol.io/specification/2026-07-28
  - Specification changelog: https://modelcontextprotocol.io/specification/2026-07-28/changelog
  - Announcement: https://blog.modelcontextprotocol.io/posts/2026-07-28/
- MCP Python SDK Repository & Releases:
  - Repository: https://github.com/modelcontextprotocol/python-sdk
  - v2 Documentation: https://py.sdk.modelcontextprotocol.io/v2/
  - Installed version: `mcp==2.3.0` (with `mcp-types==2.3.0`)

## 2. Python Version Requirements
- Supported Python versions: `>=3.10`, tested and verified on Python `3.13.12`.
- Generated servers specify `requires-python = ">=3.11"` for modern typing and asyncio features.

## 3. Server Architecture (`MCPServer`)
- Class `MCPServer` lives in `mcp.server.mcpserver` (aliased in `mcp.server.mcpserver.server`).
  - In v2, `MCPServer` is the primary high-level server interface (replaces deprecated `FastMCP`).
- **Tool Registration**:
  - `server.add_tool(fn, name=None, title=None, description=None, annotations=None, structured_output=None)`
  - `@server.tool(name=None, title=None, description=None, annotations=None)` decorator.
  - Spec-derived data (descriptions, schemas) is registered into `MCPServer` via runtime dispatch or structured handlers.
- **Tool Annotations (`mcp.types.ToolAnnotations`)**:
  - `title: str | None`
  - `read_only_hint: bool | None`
  - `destructive_hint: bool | None`
  - `idempotent_hint: bool | None`
  - `open_world_hint: bool | None` (indicates interaction with external web/API resources)

## 4. Transports & Transport Security
- **stdio Transport**:
  - Running: `server.run(transport="stdio")` or `await server.run_stdio_async()`.
  - **CRITICAL STDIO RULE**: Standard output (`stdout`) MUST NEVER contain anything other than valid JSON-RPC protocol frames.
  - All application logging, debug output, and trace diagnostics must go to `sys.stderr`.
- **Streamable HTTP Transport**:
  - Running: `await server.run_streamable_http_async(host=..., port=..., transport_security=...)`.
  - Legacy HTTP+SSE is deprecated under the 2026-07-28 specification in favor of Streamable HTTP.
- **DNS Rebinding & Host/Origin Protection**:
  - Module: `mcp.server.transport_security.TransportSecuritySettings`.
  - Fields:
    - `enable_dns_rebinding_protection: bool` (default True)
    - `allowed_hosts: list[str]` (e.g. `["127.0.0.1", "localhost", "[::1]"]`)
    - `allowed_origins: list[str]`
  - If server is bound to a non-loopback address (e.g. `0.0.0.0` or public interface), authorization via `MCP_AUTH_TOKEN` is mandatory.

## 5. Client APIs (for Playground & Testing)
- **stdio client**:
  - Import: `from mcp import stdio_client, StdioServerParameters, ClientSession`
  - Usage:
    ```python
    params = StdioServerParameters(command=sys.executable, args=["server.py"], env=scrubbed_env)
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            init_res = await session.initialize()
            tools_res = await session.list_tools()
            call_res = await session.call_tool(tool_name, arguments)
    ```
- **Session Lifecycles & Statelessness**:
  - The 2026-07-28 protocol revision emphasizes stateless operations over persistent sessions.
  - Client sessions handle handshake negotiation cleanly and cleanly terminate child subprocess groups upon exit.
