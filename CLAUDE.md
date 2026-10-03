# MCP Forge

Open-source, self-hosted tool. Input: an OpenAPI/Swagger description. Output: a ready-to-run MCP server project for that API, plus a Playground to test it (mock or real API) with a protocol trace. Web app and `forge` CLI share one core library.

## Read first (the specs are the source of truth)
- `docs/01-prd.md` - what it does
- `docs/02-architecture.md` - stack, pipeline, data model, API, mapping rules, generated layout, sources
- `docs/03-security.md` - threats, defences, required tests
- `docs/04-frontend.md` - screens, tokens, states
- `docs/05-tickets.md` - build order (one ticket at a time)
- `docs/06-deployment.md` - env vars, run, backup, release

If code and docs disagree, stop and ask. Do not silently change the stack, data model or layout.

## Stack
Backend: Python 3.13, FastAPI, SQLite + SQLAlchemy 2.0 async + Alembic, Pydantic v2, Typer, Jinja2, httpx, structlog. Generated servers use the official MCP Python SDK v2 (`mcp>=2,<3`; class `MCPServer`), spec revision 2026-07-28.
Frontend: Next.js 16 (TypeScript strict), React 19, Tailwind v4, shadcn/ui, TanStack Query, Shiki.
Tooling: uv, ruff, mypy strict, pytest, hypothesis, pnpm, Vitest, Playwright. Infra: Docker Compose, GitHub Actions.
Exact versions go in `docs/versions.lock.md`. Install latest stable; never copy versions from memory.

## Folder map
`backend/src/mcp_forge/{core,templates,mock_api,playground,api,db,services,cli}`, `backend/samples`, `backend/tests`, `frontend/src`, `docs/`. Full tree: `docs/02-architecture.md` section 9.

## Commands
- `make dev` - run backend and frontend with reload
- `make test` - all tests
- `make lint` - ruff, mypy, eslint, tsc
- `make migrate` - Alembic upgrade
- `forge generate <spec> -o out/` - generate from the command line

## Always
- Work on one ticket at a time, in order. Check its "done when" before moving on. Commit as `ticket NN: <title>`.
- Write tests with the code. Run lint and tests before each commit.
- Spec text (names, descriptions, examples) goes only into `tools.json`. Generated source comes only from fixed templates and validated identifiers.
- Safe defaults: read-only tools on, writes off, private network targets blocked, credentials only from environment variables.
- Read the MCP SDK and spec docs before touching server or client code. Record facts in `docs/sdk-notes.md`.
- In stdio mode print nothing to stdout except protocol messages; log to stderr.
- Keep generation deterministic (same input, same bytes).
- Use real, measured numbers in docs and benchmarks.

## Never
- Never put spec-derived text into Python source, `eval`, `exec` or template names.
- Never store or log credentials, tokens or response bodies from live calls.
- Never follow remote `$ref` or fetch URLs without the SSRF guard.
- Never build SQL with string formatting.
- Never enable write or delete tools by default.
- Never add telemetry, analytics, external fonts or third-party scripts.
- Never add features or dependencies that are not in the docs without asking.
- Never expose Playground or the app on a network without an access token.
