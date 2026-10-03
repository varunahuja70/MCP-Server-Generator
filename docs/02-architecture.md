# 02 - Architecture

Reads: `01-prd.md`. Every choice below exists to satisfy a behaviour in the PRD.

## 1. Principles

1. **Data and code never mix.** Everything that comes from the uploaded spec (names, descriptions, examples) lives in a JSON data file. It is never pasted into source code. The generated code is made only from fixed templates and validated identifiers. This single rule removes the biggest risk of a code generator.
2. **One internal model.** Every input format is converted into one internal model (the "IR"). Mapping, review, rendering and the Playground all read the IR, never the raw spec.
3. **Safe by default.** Read-only tools on, write tools off, credentials never saved, private network targets blocked, descriptions scanned.
4. **The core is a library.** Web app and command line are thin shells over the same core library, so behaviour is identical.
5. **Generated projects stand alone.** A generated server has no dependency on MCP Forge. Its small runtime is copied into the project and tested here.
6. **Measure, do not guess.** Performance and compatibility claims come from real runs.

## 2. Stack

Versions marked **verified** were checked on 2026-10-04 from the sources in section 10. Versions marked **pin at setup** were not verified here: the build agent installs the latest stable release, records the real version in `docs/versions.lock.md`, and never copies a version from memory.

| Layer | Choice | Version | Why |
|---|---|---|---|
| Protocol targeted | MCP specification | **verified** current revision `2026-07-28` (stateless core, no sessions; HTTP+SSE transport deprecated; replaced `2025-11-25`) | Generated servers must speak the current revision and still work with older clients |
| MCP SDK (generated servers and Playground client) | Official Python SDK, package `mcp` | **verified** v2 stable (2.0.0 released 2026-07-28; 2.2.0 seen later). Generated projects pin `mcp>=2,<3`. | Same SDK is both server and client; serves 2026-07-28 and earlier clients from one server over stdio and Streamable HTTP. Note: its `FastMCP` class is renamed `MCPServer` (module `mcp.server.mcpserver`) and protocol fields are snake_case in Python. Read the SDK docs before coding. |
| Input spec formats | Swagger 2.0, OpenAPI 3.0.x, 3.1.x, 3.2.x | **verified** latest OpenAPI is 3.2.1 (2026-09-10); 3.2 is a small, 3.1-compatible step | Covers what real APIs publish |
| Language (app + core) | Python | 3.13 (use 3.14 only if every dependency installs cleanly) | Strong parsing and templating ecosystem; same language as the generated output |
| Web framework | FastAPI | **verified** 0.136.x line (0.136.3 seen). Pin at setup | Async, typed, OpenAPI docs for the app's own API |
| Server | Uvicorn | pin at setup | |
| Validation / settings | Pydantic v2 + pydantic-settings | **verified** 2.12+ line. Pin at setup | |
| Database | SQLite (WAL mode) via SQLAlchemy 2.0 async + aiosqlite, Alembic migrations | **verified** SQLAlchemy 2.0.x stable (2.1 is beta: do NOT use). Pin the rest at setup | Single-user self-hosted tool: no database server to run |
| CLI | Typer | pin at setup | Typed, simple commands sharing the core |
| Spec parsing | PyYAML (`safe_load` only, wrapped by a size/alias guard), `openapi-spec-validator` and `jsonschema` (with the `referencing` library) | pin at setup. Confirm the validator supports 3.2 (the python-openapi validator project has a 3.2 validator class) | Standard, maintained validators |
| Templating | Jinja2 with `StrictUndefined`, autoescape off, custom safe filters | pin at setup | Code generation from fixed templates |
| Code formatting of output | ruff (format + lint) run on generated Python | pin at setup | Clean, readable generated code |
| HTTP client | httpx (async) | pin at setup | Used by the Playground, mock checks and the generated runtime |
| Process isolation (Playground) | Python `asyncio` subprocess + `resource` limits on Linux/macOS | stdlib | No extra service |
| Logging | structlog (JSON) with redaction filter | pin at setup | |
| Tooling | uv, ruff, mypy (strict), pytest, pytest-asyncio, respx, hypothesis (for hostile-input fuzzing), coverage | pin at setup | |
| Frontend | Next.js (App Router, TypeScript strict), React 19.x | **verified** Next.js 16.x (16.3.6 with React 19.3.0 reported Sept 2026). Pin: `npm view next version` | Matches owner's stack |
| UI | Tailwind CSS v4, shadcn/ui, lucide-react | pin at setup | Premium minimal look |
| Frontend data | TanStack Query | pin at setup | |
| Code viewer | Shiki (syntax highlighting) | pin at setup | File browser for generated output |
| Schema form | A small in-repo JSON Schema form renderer (string, number, integer, boolean, enum, array, object, oneOf/anyOf basics, fallback raw JSON editor) | in-repo | Avoids a heavy dependency and gives full control of states |
| Frontend tests | Vitest + Testing Library, Playwright (one smoke flow) | pin at setup | |
| Node tooling | Node LTS current at setup, pnpm | pin at setup | |
| Packaging | Docker (multi-stage, non-root) + Docker Compose; Python package for CLI (`uvx`/`pipx` install) | pin at setup | |
| CI | GitHub Actions | n/a | Lint, types, tests, audits, build |

**External services and cost:** none required. No paid APIs. No model provider calls in V1. The only network access is to the user's own target API when they choose "real API" in the Playground, and to a spec link the user provides.

## 3. System overview

```
Browser (Next.js dashboard)  ──HTTP──>  Forge API (FastAPI)  ──>  Core library
Terminal (forge CLI)         ──────────────────────────────────>  Core library

Core library pipeline:
  Ingest ─> Parse+Validate ─> Normalize (IR) ─> Map to tools ─> Review (lint)
        ─> Render project ─> Check output ─> Package (zip + file tree)

Playground (separate concern):
  Forge API ─> spawn generated server (subprocess, scrubbed env, limits)
            ─> MCP client (official SDK) over stdio
            ─> optional Mock API (in-process HTTP server built from the IR)
            ─> trace recorder (every protocol message, timing) ─> stream to browser
```

Data flow for one generation:
1. **Ingest** reads text from upload, paste or link (with all safety limits), detects JSON or YAML.
2. **Parse + validate** loads with a safe loader, checks it against the right OpenAPI version, resolves local `$ref`s (remote refs are off by default), and reports errors with locations.
3. **Normalize** produces the IR: API info, servers, security schemes, operations (method, path, parameters, request body, responses, tags, deprecation), and a resolved JSON Schema for each input. Swagger 2.0 and all OpenAPI versions end up in the same shape.
4. **Map** turns each enabled operation into a tool definition (section 6).
5. **Review** runs lint rules (section 7) over the IR and the tool set.
6. **Render** writes the project files from fixed templates plus `tools.json` (all spec-derived text).
7. **Check output** compiles every generated Python file (`ast.parse`), runs `ruff format` and a lint pass, validates `tools.json` against a schema, and runs the generated project's own tests when a Python environment is available (always in CI).
8. **Package** zips the project with a checksum and records a build row.

## 4. Data model (SQLite)

IDs are UUIDv7 text. Times are UTC ISO strings.

**project**: id, name, slug (unique), created_at, updated_at, archived_at.

**spec_version**: id, project_id, version_no, source_type (`file` | `paste` | `url` | `sample`), source_ref (file name or URL, no credentials in URLs), format (`json` | `yaml`), spec_kind (`swagger2` | `oas30` | `oas31` | `oas32`), sha256, raw_text (stored as text, size capped), operation_count, created_at. Unique on (project_id, version_no).

**project_settings** (one row per project): project_id (pk), base_url, timeout_s (default 30), max_response_chars (default 20000), retry_safe_requests (bool, default true), max_retries (default 2), naming_style (`snake` default), include_writes_default (false), auth_mapping (json: scheme name to environment variable names), transports (json list, default `["stdio","streamable-http"]`), tool_prefix (nullable).

**operation_config**: project_id, operation_key (stable key: `METHOD path` or `operationId`), enabled (bool), tool_name_override (nullable), description_override (nullable), group_override (nullable). Primary key (project_id, operation_key). Survives re-upload when the operation still exists.

**review_finding**: id, build_id (nullable), project_id, spec_version_id, severity (`error` | `warning` | `info`), code, message, operation_key (nullable), suggestion, acknowledged (bool), created_at.

**build**: id, project_id, spec_version_id, build_no, status (`queued` | `running` | `succeeded` | `failed`), tool_count, warning_count, generator_version, artifact_path, artifact_sha256, error_message_safe, created_at, finished_at.

**playground_session**: id, build_id, target (`mock` | `live`), status (`starting` | `running` | `stopped` | `failed`), started_at, ended_at, exit_info.

**trace_event**: id, session_id, seq, direction (`client_to_server` | `server_to_client` | `stderr`), message_json (redacted, size capped), duration_ms (nullable), created_at. Cleaned up on session delete and by retention (default 7 days).

**app_setting**: key, value (json). Holds `access_token_hash` (when exposed mode is configured), retention days, flags.

Credentials for the live target are **never** stored: they exist only in the memory of the Playground session and the environment of its subprocess.

## 5. Forge API surface (all under `/api`)

Auth: none in local mode (bound to 127.0.0.1). In exposed mode every route except `/healthz` requires the access-token session (see `03-security.md`).

| Group | Endpoints |
|---|---|
| Samples | `GET /samples`, `POST /projects/from-sample` |
| Projects | `GET/POST /projects`, `GET/PATCH/DELETE /projects/{id}` (delete needs confirmation body) |
| Spec | `POST /projects/{id}/specs` (upload, paste or URL), `GET /projects/{id}/specs`, `GET /projects/{id}/specs/{vid}`, `GET /projects/{id}/specs/{vid}/diff?against=` |
| Operations | `GET /projects/{id}/operations` (with risk labels and current selection), `PUT /projects/{id}/operations` (bulk selection, renames, descriptions), `POST /projects/{id}/operations/preset` (`read-only`, `by-tag`) |
| Settings | `GET/PUT /projects/{id}/settings` |
| Review | `POST /projects/{id}/review` (returns findings), `POST /projects/{id}/review/acknowledge` |
| Builds | `POST /projects/{id}/builds`, `GET /projects/{id}/builds`, `GET /builds/{id}`, `GET /builds/{id}/files` (tree), `GET /builds/{id}/files/content?path=`, `GET /builds/{id}/download`, `GET /builds/{id}/connect` (snippets) |
| Playground | `POST /playground/sessions`, `GET /playground/sessions/{id}`, `GET /playground/sessions/{id}/tools`, `POST /playground/sessions/{id}/call`, `GET /playground/sessions/{id}/trace` (server-sent events), `DELETE /playground/sessions/{id}` |
| Ops | `GET /healthz`, `GET /readyz`, `GET /version` |

Errors use one shape: `{"error": {"code", "message", "details"}}` with stable codes, so the frontend and CLI can handle them. `/api/docs` (interactive docs) only when `ENV=development`.

## 6. Mapping rules (operation to tool)

**Selection.** Skip deprecated operations by default (info finding). Safe default: `GET` and `HEAD` enabled; `POST`, `PUT`, `PATCH`, `DELETE` disabled until the user enables them. Operations using unsupported features (multipart or file upload, callbacks, webhooks, streaming responses) are marked `skipped` with a reason.

**Names.** Prefer `operationId`; otherwise `method_path_words`. Convert to lower `snake_case`, replace everything outside `[a-z0-9_]`, must start with a letter, maximum 64 characters. Optional prefix from settings. Collisions get a numeric suffix and an info finding. Reserved words and names that clash with runtime internals are renamed. A name is **validated against the regex `^[a-z][a-z0-9_]{0,63}$` and that check is the only gate before it is used as an identifier**.

**Descriptions.** `summary` + `description`, plus short parameter notes. Control characters, invisible Unicode (zero-width, bidi overrides, tag characters) are stripped. Markdown is flattened to plain text. Length capped (default 1,000 characters per tool, 300 per parameter). The user may override. The review step scans the final text.

**Input schema.** One flat JSON object schema per tool: path, query and header parameters become top-level properties (name clashes get a location prefix); the request body becomes a `body` property (object schema) or, for small flat bodies (default: up to 8 properties), is flattened into top-level properties. `required` is computed correctly. `$ref`s are fully resolved, circular references are cut at a depth limit (default 6) and replaced by a generic object with a note, and every schema is size capped. Output is plain JSON Schema compatible with the MCP tool `inputSchema`.

**Annotations.** `GET`/`HEAD`: read-only. `DELETE`: destructive. `PUT`/`DELETE`: idempotent. All: open-world (they reach an external system). Set through the SDK's tool annotation support.

**Authentication.** Security schemes map to environment variables in the generated server: API key (header, query or cookie location), HTTP bearer, HTTP basic, OAuth2 client-credentials (token fetched and cached by the runtime). Other flows are listed as unsupported with a clear note. Each operation's required scheme(s) are recorded in `tools.json`.

**Parameters and bodies in the runtime.** Path parameters are URL-encoded; query `style`/`explode` for arrays and simple objects supported; JSON and form-urlencoded bodies supported; header parameters supported (names validated); multipart not supported in V1.

**Responses.** Success body returned as text (pretty JSON when JSON), truncated at `max_response_chars` with a visible truncation note and the original size. Non-2xx responses become a tool error result that includes status, a short scrubbed body excerpt and a hint. Network errors and timeouts become tool errors with no stack traces. Safe methods retry on timeouts and `429`/`503` with backoff, honouring `Retry-After`, up to `max_retries`.

## 7. Review (lint) rules

| Code | Severity | Meaning |
|---|---|---|
| `SPEC-001` | error | Spec invalid (blocks) |
| `SPEC-002` | warning | Feature not supported, operation skipped |
| `SEC-001` | error | Invisible or bidirectional control characters found in names or descriptions (stripped; user must acknowledge) |
| `SEC-002` | warning | Description contains instruction-like text aimed at an AI agent (patterns such as "ignore previous", "do not tell the user", "send this to", hidden-action wording, URLs inside descriptions). Matched by a maintained pattern list with tests. |
| `SEC-003` | warning | Write or delete tool enabled |
| `SEC-004` | warning | Server URL points to a private or local address |
| `SEC-005` | info | No authentication scheme found for an API that looks private |
| `QUAL-001` | warning | Missing or very short description |
| `QUAL-002` | warning | More than 40 tools enabled (configurable) |
| `QUAL-003` | info | Name collision resolved |
| `QUAL-004` | warning | Input schema very large or cut at depth limit |
| `QUAL-005` | info | Operation deprecated |
| `QUAL-006` | warning | Ambiguous names (two tools whose descriptions are near-duplicates) |

Errors block generation until acknowledged. Warnings never block.

## 8. Generated project layout

```
<slug>-mcp/
├── pyproject.toml            (name, version, requires-python from SDK minimum, deps: mcp>=2,<3, httpx, pydantic)
├── README.md                 (what it is, run it, connect it, env vars, tool list)
├── .env.example              (variable names only, no values)
├── Dockerfile                (multi-stage, non-root)
├── server.py                 (generated: server object, tool registration loop, transport selection, Host/Origin checks)
├── tools.json                (ALL spec-derived data: names, descriptions, schemas, operation bindings, security)
├── runtime/                  (static, tested in this repo, copied as is)
│   ├── __init__.py
│   ├── config.py             (env loading, base URL, limits)
│   ├── auth.py               (api key, bearer, basic, client credentials with token cache)
│   ├── request_builder.py    (path/query/header/body assembly, encoding)
│   ├── client.py             (httpx client, retries, timeouts, SSRF guard for private targets)
│   ├── response.py           (shaping, truncation, error mapping, secret scrubbing)
│   └── logging.py            (redaction, stderr only)
└── tests/
    ├── test_manifest.py      (tools.json valid, names unique and valid)
    ├── test_runtime.py       (request building against a recorded mock)
    └── test_server.py        (lists tools and calls one through the SDK client against the mock)
```

Important: with stdio, **nothing may be printed to stdout except protocol messages**. Logging goes to stderr only. A test enforces this.

Transport: `python server.py` (stdio, default), `python server.py --http --host 127.0.0.1 --port 8000` (Streamable HTTP). If the host is not loopback the server refuses to start unless `MCP_AUTH_TOKEN` is set, and then requires `Authorization: Bearer` on every request. Host and Origin headers are validated against an allow-list to block DNS-rebinding style attacks. Use the SDK's own transport and security options when they exist; read its docs.

## 9. Forge repository layout

```
mcp-forge/
├── CLAUDE.md  AGENTS.md  README.md  LICENSE  CONTRIBUTING.md  SECURITY.md
├── .env.example  Makefile  docker-compose.yml  docker-compose.dev.yml
├── .github/workflows/ci.yml  .github/dependabot.yml
├── backend/
│   ├── pyproject.toml  alembic.ini  Dockerfile
│   ├── src/mcp_forge/
│   │   ├── config.py  logging_setup.py  errors.py  version.py
│   │   ├── core/
│   │   │   ├── ingest/        (sources.py, limits.py, detect.py)
│   │   │   ├── parse/         (loader.py, validate.py, refs.py)
│   │   │   ├── ir/            (models.py, normalize_swagger2.py, normalize_oas3.py, schema_tools.py)
│   │   │   ├── mapping/       (naming.py, tools.py, annotations.py, auth_map.py, presets.py)
│   │   │   ├── review/        (engine.py, rules_sec.py, rules_quality.py, patterns.py)
│   │   │   ├── render/        (renderer.py, filters.py, check_output.py, package.py)
│   │   │   ├── diff.py        (spec version diff)
│   │   │   └── security/      (ssrf.py, safe_yaml.py, paths.py, redact.py, unicode.py)
│   │   ├── templates/server_project/   (server.py.j2, pyproject.toml.j2, README.md.j2, Dockerfile.j2, .env.example.j2, tests/*.j2, runtime/*.py static)
│   │   ├── mock_api/          (builder.py, data_gen.py, server.py)
│   │   ├── playground/        (manager.py, sandbox.py, client.py, trace.py)
│   │   ├── api/               (app.py, deps.py, routes/*.py, schemas/*.py, middleware.py)
│   │   ├── db/                (base.py, session.py, models/*.py)
│   │   ├── services/          (projects.py, builds.py, review.py, retention.py)
│   │   └── cli/               (main.py: forge check | review | generate | serve | samples)
│   ├── samples/               (bookshop.openapi.yaml, tasks.openapi.json, legacy-swagger2.json, hostile/*.yaml)
│   ├── migrations/
│   └── tests/                 (unit/, integration/, security/, golden/, perf/)
├── frontend/
│   ├── package.json  next.config.ts  Dockerfile
│   └── src/{app,components,lib,styles}
└── docs/                      (this spec, versions.lock.md, benchmarks.md)
```

## 10. Key decisions and trade-offs

| Decision | Chosen | Rejected | Reason |
|---|---|---|---|
| Generated tool logic | Static tested runtime + `tools.json` data | One hand-shaped Python function per operation | Immune to code injection from the spec; runtime is unit tested once; trade-off: tool handlers are less "hand-written looking". The README of the output explains the layout. |
| Output language V1 | Python | Python and TypeScript at once | Half the surface to test; TypeScript follows after V1 (the TypeScript SDK v2 packages `@modelcontextprotocol/server` etc. exist, verified) |
| Database | SQLite | PostgreSQL | One user, local first, zero setup |
| Remote `$ref` | Off by default | On | Remote fetch is an SSRF and data-leak path; can be enabled per project with the SSRF guard on |
| Protocol era | Serve 2026-07-28 and earlier clients (SDK does it) | 2026-07-28 only | Many clients still use older handshakes; the v2 SDK handles both |
| Transport | stdio default + Streamable HTTP | Legacy HTTP+SSE | HTTP+SSE is deprecated in the current revision |
| Playground isolation | Subprocess with scrubbed env and limits | Run in the Forge process; or Docker per session | In-process is unsafe; Docker per session needs a Docker socket (worse); subprocess is the best size/safety fit. Disable-able. |
| AI help | None in V1 | LLM-written descriptions | Avoids keys, cost, and prompt-injection loops; planned as opt-in later |
| Mock API | Built from IR schemas and examples | Require a real API | Safe demo with no credentials; deterministic tests |

## 11. Sources (checked 2026-10-04)

- MCP specification, current revision 2026-07-28 and its changelog: https://modelcontextprotocol.io/specification/2026-07-28/changelog ; release announcement https://blog.modelcontextprotocol.io/posts/2026-07-28/ ; release tag https://github.com/modelcontextprotocol/specification/releases/tag/2026-07-28
- MCP Python SDK v2.0.0 stable (2026-07-28), `FastMCP` renamed `MCPServer`, built-in client: https://github.com/modelcontextprotocol/python-sdk/releases ; docs https://py.sdk.modelcontextprotocol.io/v2/ ; later 2.2.0 reported in https://github.com/homeassistant-ai/ha-mcp/issues/2464
- MCP TypeScript SDK v2 split packages (`@modelcontextprotocol/server`, `client`, `core`, 2.0.0): https://github.com/punkpeye/fastmcp/issues/300 ; Vercel handler note https://vercel.com/changelog/latest-mcp-spec-now-supported-in-mcp-handler
- OpenAPI Specification 3.2.1 (2026-09-10) and earlier versions: https://spec.openapis.org/oas/v3.2.1.html ; releases https://github.com/OAI/OpenAPI-Specification/releases ; 3.2 overview https://redocly.com/blog/openapi-3-2.md
- OpenAPI schema validator with a 3.2 validator class: https://github.com/python-openapi/openapi-schema-validator/pull/263/files
- FastAPI 0.136.3 (2026-05-23): https://pepy.tech/project/fastapi
- Next.js 16.3.6 and React 19.3.0 (Sept 2026): https://www.achromatic.dev/changelog/september-2026-nextjs-react-update ; 16.x line https://releases.sh/vercel/nextjs.md
- SQLAlchemy 2.0.x stable, 2.1 beta: https://www.sqlalchemy.org/blog
- Pydantic 2.12 and Python 3.14 support notes: https://github.com/Randroids-Dojo/typescript-and-python-bootstrap/pull/79
