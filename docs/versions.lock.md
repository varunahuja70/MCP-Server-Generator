# MCP Forge Dependency Versions Lock

Generated on: 2026-10-04
All versions were inspected and resolved directly using the package managers (`uv` and `pnpm`). Never copied from memory.

## Backend Dependencies (Python 3.13.12, uv 0.12.5)

| Package | Pinned Version | Resolution Command / Source |
|---|---|---|
| `mcp` | `2.3.0` | `uv pip install mcp>=2,<3` |
| `mcp-types` | `2.3.0` | transitive dependency of `mcp` |
| `fastapi` | `0.142.2` | `uv pip install fastapi` |
| `uvicorn` | `0.54.0` | `uv pip install uvicorn[standard]` |
| `sqlalchemy` | `2.0.54` | `uv pip install sqlalchemy>=2.0.0,<2.1.0` (2.1 beta excluded per spec) |
| `aiosqlite` | `0.22.1` | `uv pip install aiosqlite` |
| `alembic` | `1.20.0` | `uv pip install alembic` |
| `pydantic` | `2.13.5` | `uv pip install pydantic>=2.10.0` |
| `pydantic-settings` | `2.15.0` | `uv pip install pydantic-settings` |
| `typer` | `0.27.2` | `uv pip install typer` |
| `jinja2` | `3.1.6` | `uv pip install jinja2` |
| `httpx` | `0.28.1` | `uv pip install httpx` |
| `structlog` | `26.1.0` | `uv pip install structlog` |
| `pyyaml` | `6.0.3` | `uv pip install pyyaml` |
| `jsonschema` | `4.26.0` | `uv pip install jsonschema` |
| `referencing` | `0.37.0` | `uv pip install referencing` |
| `openapi-spec-validator` | `0.9.0` | `uv pip install openapi-spec-validator` |
| `ruff` | `0.16.10` | `uv pip install ruff` |
| `mypy` | `2.4.0` | `uv pip install mypy` |
| `pytest` | `9.1.1` | `uv pip install pytest` |
| `pytest-asyncio` | `1.4.0` | `uv pip install pytest-asyncio` |
| `respx` | `0.23.1` | `uv pip install respx` |
| `hypothesis` | `6.168.3` | `uv pip install hypothesis` |
| `coverage` | `7.16.2` | `uv pip install coverage` |

## Frontend Dependencies (Node 24.7.0, pnpm 10.17.1)

| Package | Pinned Version | Resolution Command / Source |
|---|---|---|
| `next` | `16.3.8` | `pnpm info next version` |
| `react` | `19.3.0` | `pnpm info react version` |
| `react-dom` | `19.3.0` | `pnpm info react-dom version` |
| `tailwindcss` | `4.0.0` | `pnpm install tailwindcss` |
| `@tailwindcss/postcss` | `4.0.0` | `pnpm install @tailwindcss/postcss` |
| `@tanstack/react-query` | `5.62.7` | `pnpm install @tanstack/react-query` |
| `lucide-react` | `1.16.0` | `pnpm install lucide-react` |
| `shiki` | `3.1.0` | `pnpm install shiki` |
| `vitest` | `3.0.0` | `pnpm install vitest` |
| `typescript` | `5.7.2` | `pnpm install typescript` |
| `eslint` | `9.16.0` | `pnpm install eslint` |
