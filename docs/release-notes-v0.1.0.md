# Release Notes - v0.1.0

**Release Date:** October 4, 2026  
**Status:** Initial Stable Release

MCP Forge v0.1.0 is the first release of the self-hosted tool that converts OpenAPI and Swagger specifications into ready-to-run Model Context Protocol (MCP) server projects with an interactive testing Playground.

---

## Highlights

### 1. Multi-Standard OpenAPI & Swagger Support
- Native parsing and schema validation for **Swagger 2.0**, **OpenAPI 3.0.x**, **OpenAPI 3.1.x**, and forward compatibility with **OpenAPI 3.2 draft**.
- Automatic resolution of local `$ref` pointers with circular reference severing and depth limits.
- Ingestion from uploaded files, direct text paste, and remote HTTP/HTTPS links protected by an SSRF validator.

### 2. Bulletproof Code / Data Separation
- **Zero code generation from spec strings:** Arbitrary specification text resides strictly in `tools.json`.
- Python server logic is powered by a static, unit-tested runtime library and pre-compiled Jinja2 templates.
- Strict identifier gate enforcing ASCII tool names matching `^[a-z][a-z0-9_]{0,63}$`.
- Python AST security scanner validating that generated source code contains zero dynamic execution primitives (`eval`, `exec`, `subprocess`, `os.system`).

### 3. Built-in Security and Quality Review Engine
- Automated rule evaluation across 12 checks:
  - `SEC-001`: Invisible / bidi unicode character detection
  - `SEC-002`: Prompt injection instruction detection
  - `SEC-003`: Mutating / destructive write operations warning
  - `SEC-004`: Private network and cloud metadata server targets
  - `SEC-005`: Unauthenticated private API detection
  - `SEC-006`: Leaked API keys or credential patterns
  - `QUAL-001` through `QUAL-006`: Description quality, operation IDs, status code schemas.

### 4. Interactive Testing Playground
- Test generated MCP tools directly from the browser before exporting.
- **In-process Mock API server:** Deterministic response synthesis conforming to schema types and examples.
- **Live Target Mode:** Real-time API invocations with confirmation modals for mutating actions.
- Real-time Server-Sent Events (SSE) protocol trace stream displaying incoming and outgoing JSON-RPC frames.
- Memory-only credential handling that completely scrubs API tokens from client memory after session initialization.

### 5. Multi-Client Integration Snippets
- Instant connection snippets and instructions for **Claude Desktop**, **Cursor**, **Stdio CLI**, and **Streamable HTTP**.
- Deterministic ZIP archive packaging with normalized 2026-01-01 timestamps and reproducible SHA256 hashes.

### 6. Dual Web UI and Typer CLI
- Next.js 16 + React 19 + Tailwind v4 web dashboard.
- Typer CLI (`forge check`, `forge review`, `forge generate`, `forge serve`, `forge samples`, `forge wipe`) with standard exit codes for CI/CD automation.

---

## Upgrade and Installation
```bash
# Python CLI installation
pip install mcp-forge==0.1.0

# Or via uv
uv tool install mcp-forge==0.1.0
```
