# MCP Forge - Full Spec Bundle

This single file contains every spec file. Each file starts with a marker line `<!-- FILE: path -->` and ends with `<!-- END FILE -->`. Split them into the paths shown.

<!-- FILE: CLAUDE.md -->
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

<!-- END FILE -->

<!-- FILE: AGENTS.md -->
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

<!-- END FILE -->

<!-- FILE: docs/01-prd.md -->
# 01 - Product Requirements (PRD)

Working name: **MCP Forge**
Status: Draft v1
Track: Full (saved projects, a database, a testing UI). No payments, no multi-user accounts.

> Rule for this document: behaviour only. No framework or library names. Standards names (OpenAPI, MCP) are the product's subject and are allowed. The stack is chosen in `02-architecture.md`.

## One-liner

Give MCP Forge an API description (an OpenAPI file or link) and it produces a ready-to-run MCP server for that API, plus a built-in testing screen where you can try every tool before you ship it.

## Problem

Most companies and developers have a working HTTP API. AI agents (Claude and others) can only use it comfortably if it is exposed as an MCP server. Today, making one means:

- reading the MCP documentation and the SDK,
- hand-writing one tool per endpoint,
- guessing how to turn parameters, authentication and errors into something an agent understands,
- finding out only later that the server is unsafe (it exposes delete endpoints), too big (hundreds of tools confuse agents) or badly described (agents call it wrongly).

There is no quick way to preview how an agent will see the API, and no safe way to test the server without wiring it into a real AI app first.

## Target user

**Primary:** A developer or small team that owns or uses an HTTP API with an OpenAPI description and wants AI agents to use it, without learning every detail of MCP.

**Secondary:** Developers who want to study clean generated code; open-source contributors; API providers publishing an MCP server for their customers.

**Not for:** People who need to turn a website into an API (no scraping), or teams that need a hosted multi-tenant platform with accounts and billing.

## Core features (V1)

### 1. Bring an API description in
- Accept an OpenAPI file in JSON or YAML by upload, by pasted text, or by link.
- Supported versions: Swagger 2.0, OpenAPI 3.0, 3.1 and 3.2.
- Show clear, readable errors when the file is invalid, too large, or uses unsupported parts. Never crash on bad input.
- Provide built-in sample APIs so a first-time visitor can try everything without owning a spec.

### 2. Understand the API
- Show a summary: name, version, servers, number of operations, groups (tags), authentication methods found.
- Show every operation with method, path, summary and risk label (read-only, writes data, destructive).

### 3. Decide what the agent can see
- Each operation becomes at most one tool. The user picks which ones are enabled.
- **Safe by default:** read-only operations start enabled; anything that changes or deletes data starts disabled and needs a deliberate switch.
- The user can rename a tool, rewrite its description, and group tools by tag.
- A visible warning appears when too many tools are enabled, because agents work worse with very large tool lists. The tool offers presets (for example "read-only", "by tag").
- Each tool carries honest hints about itself (read-only, destructive, repeat-safe) so agents and apps can decide how careful to be.

### 4. Quality and safety review
- A checklist-style review runs before generation and lists findings with a severity and a suggested fix. It checks for:
  - missing or very short descriptions,
  - name clashes and unclear names,
  - oversized input definitions,
  - unsupported features that will be skipped,
  - **suspicious description text** that tries to instruct an AI agent (hidden characters, "ignore previous instructions" style text), since descriptions go straight into an agent's context,
  - write or delete tools that are enabled.
- Blocking findings must be acknowledged before generation. The user can always see exactly what was changed or removed.

### 5. Connect the API's authentication
- Detect how the API authenticates: API key (header or query), bearer token, basic login, or machine-to-machine token request.
- The generated server reads credentials from its environment at run time. Credentials are never written into generated files.
- The user can set the API base address, request timeout, response size limit and retry behaviour for safe, repeatable requests.

### 6. Generate the server
- Produce a complete, readable, runnable project: the server, the tool definitions, setup instructions, an example environment file, a container file, and tests.
- The server supports running locally as a command for desktop AI apps, and over the network for remote use.
- Every generation is saved as a numbered build with its warnings. Regenerating after a spec change keeps the user's choices (renames, enabled tools) where the operation still exists, and lists what changed.
- Download as one archive, or browse the files in the app.
- Show copy-paste connection snippets for common AI apps and tools.

### 7. Test it before shipping (the Playground)
- Start the generated server inside the app and list its tools exactly as an agent would see them.
- Fill a form built from each tool's input definition, run the tool, and see the result and any error.
- Show the raw protocol messages exchanged for every call, with timings.
- Two targets: a **built-in mock of the API** (no credentials, no risk, answers shaped like the spec says) or the **real API** (credentials typed in for the session only, never saved).
- Clearly warn before any call that changes data on the real API.

### 8. Command-line use
- Everything needed for automation also works without the web screen: check a spec, review it, generate a project, and start the app. This lets teams run generation in their build pipeline.

### 9. Project history
- Saved projects list with spec versions, builds and settings. Delete a project and all its data with one confirmed action.

### 10. Safe by design for self-hosting
- Runs on the user's own machine or server. By default only reachable from that machine. If exposed on a network, it requires an access token.
- No usage tracking or data sent anywhere.

## Non-goals (V1)

- No scraping of human documentation pages. Input is an OpenAPI description.
- No other spec formats yet (Postman collections, GraphQL, gRPC are later).
- No AI-written descriptions in V1 (no calls to model providers). Users edit descriptions by hand.
- Only one output language in V1 (Python). A TypeScript output is a later feature.
- No file upload or multipart request support in generated tools (such operations are listed as skipped).
- No full browser-based login flows (authorization-code style) for the target API.
- No hosted version, no user accounts, no billing.
- No publishing to package registries from inside the app.

## Main user flows

**Quick try (first visit)**
1. Choose a sample API.
2. See its operations and the safe default selection.
3. Press Generate, then open the Playground.
4. Run a tool against the mock API and see the result and protocol trace.

**Real use**
1. Create a project from a file or link.
2. Fix any invalid-spec errors shown.
3. Review operations, enable what the agent should have, rename and re-describe.
4. Set base address and authentication mapping.
5. Read the review findings, resolve or acknowledge them.
6. Generate, test in the Playground against the mock, then against the real API with a read-only call.
7. Download the project or copy the connection snippet.

**API changes**
1. Open the project, upload the new spec version.
2. See added, removed and changed operations. Previous choices carry over.
3. Generate a new build.

## Success criteria

- A first-time user goes from opening the app to a successful mock tool call in under 3 minutes.
- At least five varied real-world OpenAPI files (small, large, Swagger 2.0, 3.0, 3.1) generate without errors, or fail with a clear explanation.
- Every generated project starts, lists its tools, and passes its own tests.
- A deliberately hostile spec (code-like text in names and descriptions, huge nesting, circular references, bad encoding) never causes code execution, a crash, or a hang.
- No credential ever appears in generated files, saved data, logs or the browser's storage.
- Parsing and generating a 5,000-operation spec finishes in a reasonable time on a normal laptop (measured and written down, not guessed).
- A new developer can follow the README and have a working demo in under 10 minutes.

## Open questions

1. Final product name and repository name (working name: MCP Forge, repo `mcp-forge`).
2. Open-source licence: MIT or Apache 2.0.
3. Should the TypeScript output be the first follow-up after V1, or the Postman collection input?
4. Should a later version add optional AI-assisted description rewriting using the user's own key?

<!-- END FILE -->

<!-- FILE: docs/02-architecture.md -->
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

<!-- END FILE -->

<!-- FILE: docs/03-security.md -->
# 03 - Security

Reads: `01-prd.md`, `02-architecture.md`. MCP Forge takes **untrusted input** (specs), **generates code**, **runs that code**, and **talks to other people's APIs**. Those four facts drive everything here. Every rule must have a test (section 11).

## 1. What we protect

1. The machine and network of the person running Forge.
2. Credentials the user types for their target API.
3. The AI agents that will later use the generated servers (they trust tool descriptions and tool results).
4. The user's saved projects and specs.
5. The people who will run the generated server (it must be safe out of the box).

## 2. Modes and who can do what

| Mode | How it runs | Access |
|---|---|---|
| Local (default) | Binds to `127.0.0.1` only | Whoever can reach localhost on that machine. No login. |
| Exposed | Bound to a non-loopback address | **Access token required** (`FORGE_ACCESS_TOKEN`). The app refuses to start exposed without one. Login sets an httpOnly session cookie. Playground disabled unless `PLAYGROUND_ENABLED=true` is set explicitly. |

| Actor | Can do |
|---|---|
| Local user / authenticated owner | Everything in `/api`. |
| Anonymous (exposed mode) | `GET /healthz` and the login endpoint only. |
| Generated server's client (an AI app) | Only what that server exposes. Forge is not involved at run time. |

There is no multi-user model in V1. Projects are not separated by user.

## 3. Threats and defences

### 3.1 Hostile spec leads to code injection (highest risk)
A spec can contain names or descriptions like `"); import os; os.system("...` meant to end up in generated code.
- **Spec text never enters source code.** All spec-derived strings go into `tools.json` as JSON data. Source files are rendered from fixed templates.
- The only spec-derived values used in source are identifiers (server module name, tool names used as dictionary keys). They must match `^[a-z][a-z0-9_]{0,63}$` and are checked again by the renderer. Anything else is rejected or renamed, never escaped.
- Jinja runs with `StrictUndefined`. Templates are fixed files, never built from user text. User text is never passed to `Template(...)` or `eval`, `exec`, `compile`, or `pickle`.
- After rendering, every `.py` file is parsed with `ast.parse`; a check fails the build if the syntax tree contains calls to `eval`, `exec`, `os.system`, `subprocess` or `__import__` outside the allow-listed runtime lines.
- Fuzz tests (hypothesis) feed hostile names and descriptions through the full pipeline and assert the generated source contains none of them (they appear only in `tools.json`).

### 3.2 Hostile spec leads to denial of service
- Maximum spec size 10 MB (configurable), enforced while reading, not after.
- YAML: `safe_load` only; alias expansion limited; nesting depth limited; no custom tags. JSON: depth limited.
- `$ref` resolution: local only by default; cycle detection; maximum resolved size; maximum depth.
- Parsing and generation run with a wall-clock timeout (default 30 s) and in a worker thread/process so the API stays responsive.
- Operation count and schema count caps (default 20,000 operations) with a clear message.

### 3.3 SSRF through links and servers
Places where a URL comes from outside: spec link, remote `$ref` (if enabled), `servers` URL in the spec (used for live Playground calls and as the generated default), and URLs inside descriptions.
- Spec link fetch: `https` and `http` only. Resolve the host, **block loopback, private (RFC 1918), link-local including 169.254.169.254, multicast, reserved and unique-local IPv6**, and decimal/octal/hex IP spellings. Check again at connect time (DNS rebinding). Limit redirects to 3, re-validating each hop. Timeout 10 s, size cap, content-type check. User-Agent identifies Forge.
- The generated runtime contains the same guard and uses it for the target API unless `ALLOW_PRIVATE_TARGETS=true` is set in its environment. Local APIs are a legitimate use, so this is a documented switch, off by default, and Forge's review finding `SEC-004` tells the user.
- Credentials are never put in URLs that Forge stores or logs. URLs with embedded credentials are rejected.

### 3.4 Tool poisoning and prompt injection (the MCP-specific risk)
Descriptions go straight into an AI agent's context. A malicious or careless spec can try to steer the agent.
- Strip control characters and invisible/bidirectional Unicode from names and descriptions. Normalize Unicode (NFKC) before pattern scans.
- Pattern scan (`SEC-002`) for instruction-like text. This is a heuristic and the UI says so: it reduces risk, it does not prove safety.
- Length caps on descriptions and schema titles.
- The user sees the exact final description of each tool before generation, and can edit it.
- **Tool results are untrusted too.** The runtime returns API responses as data, truncated, and the generated README warns that API content can contain instructions. No part of Forge or the runtime ever treats response text as instructions.
- Generated servers expose only the tools in the manifest. No hidden tools, no dynamic tool changes at run time.

### 3.5 Dangerous capabilities exposed to agents
- Safe default: only read-only operations enabled. Enabling a write or delete tool shows a confirmation and a persistent badge, and raises `SEC-003`.
- Tool annotations (read-only, destructive, idempotent) are set so clients can ask for confirmation.
- The generated runtime has a per-tool and global rate limit (defaults documented, configurable) so a looping agent cannot hammer the API.
- Response size cap and request timeout on every call.

### 3.6 Credentials
- Generated projects read credentials only from environment variables. `.env.example` lists names, never values. Generated files, `tools.json`, logs and error messages never contain credential values.
- In the Playground, live credentials are accepted in the request body over the local connection, kept only in memory, passed to the subprocess environment, and discarded when the session ends. They are never written to the database, trace, logs or browser storage. The UI does not put them in URLs or the query cache.
- A redaction filter removes `Authorization` headers, cookies, bearer-looking tokens, `sk-`/`ghp_`/`AKIA`-style keys, and any value that was supplied as a credential in the current session, from logs, traces and error messages. Tests assert this.
- Stored specs can contain secrets by mistake (example tokens). The review step flags strings that look like live keys (`SEC-006`, warning) and the stored copy is only readable through the same access rules as everything else.

### 3.7 Playground sandbox (it runs generated code)
The code is ours (from fixed templates), but the data it handles is hostile, and defence in depth matters.
- Subprocess started with a **scrubbed environment**: only `PATH`, `HOME` (a temp directory), locale, and the variables the user supplied for that session. No inherited secrets.
- Working directory is a fresh temp directory per session, deleted on stop. File access only inside it by construction (no user-controlled paths).
- Limits: CPU time, memory (via `resource` limits on Linux/macOS), maximum output bytes, maximum number of messages, idle timeout (default 15 min), hard session timeout (default 2 h). Process group killed on stop and on Forge shutdown.
- A maximum number of concurrent sessions (default 3).
- Trace and stderr are size-capped, redacted and stored briefly (default 7 days).
- Live target mode requires an explicit selection and shows a clear warning before any call that is not read-only.
- In exposed mode the Playground is off unless enabled by setting.

### 3.8 Path traversal and archives
- The file browser and download use only `build_id` plus a relative path. Paths are normalized and must stay inside the build's directory. Symlinks are never created in output and never followed. `..`, absolute paths and drive letters are rejected.
- Zip files are written with fixed names from a known file list; no names come from the spec. Uploaded archives are not accepted in V1.

### 3.9 Web application protections
- Local mode: strict `Host` header allow-list (`localhost`, `127.0.0.1`, `[::1]`, the configured public host) to stop DNS-rebinding attacks from web pages.
- CORS closed by default. In local mode the frontend is same-origin through the proxy or Next.js rewrite.
- State-changing requests require a custom header `X-Forge-Request: 1` plus `Origin` check (in exposed mode also a CSRF token tied to the session). This blocks cross-site form posts.
- Security headers on the frontend: strict `Content-Security-Policy` (no inline scripts, nonces where needed), `X-Content-Type-Options`, `Referrer-Policy: same-origin`, `frame-ancestors 'none'`, `Permissions-Policy`.
- Generated file contents and spec text are always rendered as plain text in the UI (escaped), never as HTML. The code viewer treats content as text only.
- Request body size limits: 12 MB for spec upload, 1 MB elsewhere.
- Rate limits (in memory, per IP): parse/generate 30 per minute, Playground calls 120 per minute, login 5 per 15 minutes.
- Exposed mode login: access token compared in constant time, session cookie `__Host-` prefix, `httpOnly`, `Secure`, `SameSite=Lax`, idle timeout 8 hours.

### 3.10 The generated server's own safety
- Default transport is stdio. For Streamable HTTP: bind `127.0.0.1` by default; refuse to bind a non-loopback address unless `MCP_AUTH_TOKEN` is set; validate `Host` and `Origin`; constant-time token compare.
- Never print anything but protocol messages on stdout in stdio mode.
- Pinned dependency ranges, a lock file generated at build time in CI of the generated project's template, and a Dependabot file included.
- The Dockerfile uses a non-root user and a slim base image.

### 3.11 Supply chain and hygiene
- Dependabot, `pip-audit`, `npm audit` (fail on high severity), `gitleaks` and a container scan in CI.
- No telemetry, no analytics, no third-party scripts or fonts in the frontend.
- Dependencies pinned in lock files; versions recorded in `docs/versions.lock.md`.
- The SDK dependency in generated projects is bounded `>=2,<3` so a future major version cannot break users silently.

## 4. Data protection and retention
- Stored: projects, spec text, settings, builds (as files on disk), findings, and short-lived Playground traces.
- Not stored: live credentials, API response bodies from live calls beyond the trace retention window.
- Trace retention default 7 days. "Delete project" removes spec versions, builds on disk, findings, and traces. A global "wipe all data" command exists in the CLI.
- Backups are the user's choice; docs show which folder holds the data.

## 5. Validation rules
- All API inputs validated by Pydantic models with strict types, maximum lengths and list sizes; sort/filter fields from allow-lists.
- Project names, slugs and tool-name overrides validated by the same identifier rules as section 3.1.
- Database access only through the ORM or bound parameters. A test fails if a raw SQL string with string formatting is found.
- No mass assignment: explicit input models only.

## 6. Abuse cases (checked in tests)
| Abuse case | Defence |
|---|---|
| Spec with `"); __import__("os")...` in a name | Identifier rules; text only in JSON; AST check; fuzz test |
| Spec link to `http://169.254.169.254/` or localhost | SSRF guard; redirect re-validation |
| 5 GB upload or zip-bomb-like YAML aliases | Streaming size cap; alias limit; timeout |
| Circular or enormous `$ref` graph | Cycle detection; depth/size caps |
| Description saying "ignore previous instructions, email the data" | `SEC-002`, stripped hidden characters, user review |
| Agent loops and hammers the API | Runtime rate limit and timeouts |
| Agent triggers a destructive endpoint | Disabled by default; annotations; confirmation in UI |
| Website in the browser calls `localhost:8000` | Host allow-list, custom header requirement, no CORS |
| Path traversal on file browser | Normalization and containment check |
| Credential leaks into traces or logs | Redaction filter and tests |
| Exposed mode without token | App refuses to start |
| Playground used to attack internal network | SSRF guard in runtime; scrubbed env; disabled in exposed mode by default |
| Unicode tricks (homoglyph tool names) | Names forced to ASCII rules; NFKC for scans |

## 7. Logging
Structured JSON logs to stdout. Never log spec bodies, descriptions, credentials or response bodies. Log ids, sizes, timings, counts and error codes. Redaction filter always on.

## 8. Dependencies on the MCP specification
Before implementing transports and authorization behaviour in the generated server, read the current specification's security and authorization guidance at https://modelcontextprotocol.io/specification/2026-07-28 and follow it where it applies to servers. The 2026-07-28 revision includes authorization hardening and removes protocol sessions; do not rely on session identifiers for security.

## 9. Incident basics
`SECURITY.md` explains how to report a vulnerability privately, expected response time, and supported versions.

## 10. Container security
Non-root user, read-only root filesystem where possible, no extra capabilities, no published ports except the app port (bound to localhost by default in the compose file), volumes only for the data directory.

## 11. Required security tests
1. Hostile-name fuzz: generated source never contains spec text; only `tools.json` does (hypothesis, many cases).
2. Identifier gate: invalid names rejected or renamed; never escaped into code.
3. AST check fails the build for forbidden calls in generated Python.
4. YAML alias bomb, deeply nested JSON/YAML, huge file, circular `$ref`, self-referencing `allOf`: all fail fast with clear errors under the time limit.
5. SSRF matrix for spec links and redirects: loopback, private, metadata, IPv6, decimal/hex/octal forms, DNS rebinding simulation, redirect to private.
6. Invisible/bidi characters stripped; `SEC-001` raised; instruction patterns raise `SEC-002`.
7. Credential redaction: supplied credentials never appear in logs, traces, API responses, DB rows, generated files.
8. Playground sandbox: env scrubbed, limits enforced, process group killed on stop and shutdown, concurrent session cap.
9. Path traversal attempts on file browser and download all fail.
10. Host-header and cross-origin request tests (local mode); exposed mode refuses to start without token; unauthenticated calls get `401`.
11. Generated server: stdout stays clean in stdio mode; non-loopback bind without token refuses to start; bad Host/Origin rejected; rate limit works.
12. Default selection test: no write or delete tool is enabled by default for any sample spec.

<!-- END FILE -->

<!-- FILE: docs/04-frontend.md -->
# 04 - Frontend

Reads: `01-prd.md`, `02-architecture.md`. A Next.js dashboard that talks to the Forge API on the same origin.

## 1. Design direction
Premium, minimal, calm, developer-grade. Quality bar: Linear and Vercel. Dark first, light supported. Thin borders, generous whitespace, one accent colour, restrained motion. Code and JSON are first-class: monospace blocks are clean, copyable and readable. No decorative gradients, no emoji icons, no stock art.

## 2. Design tokens (`src/styles/tokens.css`, exposed through Tailwind v4 theme variables)
| Token | Dark | Light |
|---|---|---|
| background | `#09090B` | `#FFFFFF` |
| surface | `#101013` | `#FAFAFA` |
| surface-raised | `#16161A` | `#FFFFFF` |
| border | `#25252B` | `#E6E6EA` |
| text | `#ECECEF` | `#0B0B0C` |
| text-muted | `#8A8A93` | `#6A6A72` |
| accent | `#7C5CFF` | `#5B3FE0` |
| success | `#3DD68C` | `#15803D` |
| warning | `#F5A524` | `#B45309` |
| danger | `#F5555D` | `#DC2626` |
| risk-read | `#3DD68C` | `#15803D` |
| risk-write | `#F5A524` | `#B45309` |
| risk-destructive | `#F5555D` | `#DC2626` |

Fonts: Inter (UI) and JetBrains Mono (code), loaded through `next/font` (self-hosted, no external requests). Numbers use tabular figures. Type scale 12/13/14/16/20/28/36. Radius 8 cards, 6 inputs. 4 px spacing grid. Motion 150-200 ms ease-out, always respecting reduced-motion. Risk is never shown by colour alone: each badge also has a text label ("Read", "Writes", "Deletes").

## 3. Screens
1. **Home** (`/`): recent projects, "New project" button, and a "Try a sample API" strip with the bundled samples. Empty state teaches the three-step flow.
2. **New project** (`/projects/new`): three tabs - Upload, Paste, Link - plus samples. After submit: live validation result (version detected, operations count, errors with line/path). Errors are readable and point to the exact location.
3. **Project overview** (`/projects/[id]`): spec summary (name, version, servers, auth methods, tag list), operation counts by risk, latest build status, spec version history, and a stepper showing progress: Import, Tools, Settings, Review, Generate, Test.
4. **Tools** (`/projects/[id]/tools`): the central screen. Table of operations: enabled switch, method pill, path, tool name (inline editable), risk badge, group (tag), description (opens editor drawer with a live "what the agent sees" preview). Filters by tag, method, risk, text. Bulk actions and presets (Read-only, By tag). A running count of enabled tools with a warning bar over the recommended limit. Skipped operations appear greyed with the reason.
5. **Settings** (`/projects/[id]/settings`): base address, timeout, response size limit, retries, naming style, prefix, auth mapping (scheme to environment variable names), transports.
6. **Review** (`/projects/[id]/review`): findings grouped by severity with code, message, location, suggestion, and an "Acknowledge" action for blocking ones. A diff-style view shows the original vs. cleaned text when characters were stripped.
7. **Generate / Builds** (`/projects/[id]/builds`): build button, build list with status and warnings, and for each build a file browser (tree + syntax-highlighted viewer, copy button), Download archive, and a **Connect** panel with ready snippets (desktop app config, command-line client command, remote URL form) and the environment variable list. Spec change diff (added/removed/changed operations) shown when a new spec version exists.
8. **Playground** (`/projects/[id]/playground`): left - session controls (target: Mock or Live, credentials fields for live shown only for Live, Start/Stop); middle - tool list with search, and for the selected tool a generated form, Run button, result viewer (formatted text/JSON, error state); right - protocol trace (list of messages with direction, method, timing; expandable JSON; filter; copy). Live mode shows a warning banner and asks confirmation before non-read-only tools.
9. **Settings (app)** (`/settings`): version, mode (local/exposed), data location, retention, access token status, theme.
10. **Login** (`/login`): only in exposed mode.

## 4. Component inventory
shadcn/ui primitives: Button, Input, Textarea, Select, Switch, Checkbox, Dialog, Sheet, Tabs, Table, Badge, Tooltip, Toast, Skeleton, DropdownMenu, Command, Progress.
Custom: `Stepper`, `SpecDropzone`, `ValidationReport`, `OperationTable`, `RiskBadge`, `MethodPill`, `ToolNameInput`, `DescriptionEditor` (with agent-view preview), `ToolBudgetBar`, `FindingList`, `TextDiff`, `FileTree`, `CodeViewer` (Shiki, plain-text safe), `ConnectPanel`, `SchemaForm`, `ResultViewer`, `TraceList`, `TraceMessage`, `CredentialFields` (password inputs, memory-only), `ConfirmDialog` (type the project name for destructive actions), `EmptyState`, `ErrorState`, `ModeBanner`.

## 5. States (every screen defines all four)
| State | Behaviour |
|---|---|
| Loading | Skeletons matching the layout; no page-level spinners. Long operations (generate, start session) show progress text and are cancellable. |
| Empty | One sentence and the single next action (for example "Import an API description"). |
| Error | Plain language, error code in muted text, a retry button. Validation errors list location and fix hint. |
| Success | Quiet toast; the changed thing updates in place. |

Big lists (operations up to 20,000) use virtualized rows and server-side filtering. Long traces are virtualized and capped with a "load older" control.

## 6. Responsive behaviour
Desktop first, usable down to 360 px. Three-column Playground collapses into tabs (Tools / Run / Trace) below 1024 px. Sidebar collapses to a top bar with a sheet menu below 768 px. Tables scroll inside their container; the page never scrolls sideways. Touch targets 44 px minimum.

## 7. Accessibility floor
- WCAG 2.2 AA contrast in both themes.
- Full keyboard use with a visible 2 px focus ring; logical tab order; dialogs trap and restore focus; Escape closes sheets and dialogs; table rows operable by keyboard.
- Icons that carry meaning have text or `aria-label`. Risk and severity are conveyed with text, not only colour.
- Forms: labels tied to inputs, errors linked by `aria-describedby`, errors announced politely. The generated tool form follows the same rules.
- Trace and results regions are labelled; live updates use polite announcements and can be paused.
- Respect `prefers-reduced-motion` and `prefers-color-scheme`, with a manual theme switch.

## 8. Frontend rules
- TypeScript strict, no `any`. API types generated from the backend OpenAPI schema so client and server cannot drift.
- All server data via TanStack Query hooks in `src/lib/queries`; no fetch calls in components. Every state-changing call sends the `X-Forge-Request: 1` header.
- Spec text, descriptions, results and traces are rendered as escaped text only. Never `dangerouslySetInnerHTML` for any of them.
- Live credentials live only in component state while the Playground session is being created. Never in URLs, local/session storage or the query cache; fields are cleared after the request is sent.
- The schema form supports string (formats: date, date-time, email, uri), number, integer, boolean, enum, array, object, oneOf/anyOf (pick a branch), with a raw JSON fallback editor for anything unsupported. It validates before sending and shows server validation errors per field.
- No third-party scripts, analytics or external fonts. The strict CSP depends on this.
- Tests: Vitest for formatters, the schema form, risk badge logic; Playwright smoke flow (sample project, generate, mock call, see trace).

<!-- END FILE -->

<!-- FILE: docs/05-tickets.md -->
# 05 - Tickets (build order)

Reads: all earlier docs. Build in order. Each ticket ends with a **done-when** check. Run lint, type check and tests before moving on. Commit after every ticket as `ticket NN: <title>`.

Rules for every ticket: follow `03-security.md`; add tests with the code; no secrets in code; no spec text inside generated source; update `docs/versions.lock.md` whenever a dependency is added.

---

## T01 - Project setup
**Depends on:** none
**Build:** Repo skeleton from `02-architecture.md` section 9. Backend with uv, `pyproject.toml` (package `mcp_forge`, console script `forge`), ruff and mypy strict config, pytest config. Frontend with the latest stable Next.js (TypeScript strict), Tailwind v4, shadcn/ui init, ESLint, Prettier, Vitest. `Makefile` (dev, test, lint, migrate, seed, build), `.gitignore`, `.env.example`, `LICENSE` (MIT unless the owner chose otherwise), `.github/workflows/ci.yml` (lint, types, tests, pip-audit, npm audit, gitleaks), `.github/dependabot.yml`. Create `docs/versions.lock.md` listing every pinned version and the command used to get it. Read the MCP Python SDK v2 docs and note the minimum Python version and the tool-registration, transport and client APIs in `docs/sdk-notes.md` (facts only, with links).
**Files:** repo root, `backend/`, `frontend/`, `.github/`, `docs/versions.lock.md`, `docs/sdk-notes.md`
**Done when:** `make lint` and `make test` pass on the empty skeleton; `forge --help` runs.

## T02 - Config, logging and app shell
**Depends on:** T01
**Build:** `config.py` (pydantic-settings: mode local/exposed, host, port, data dir, limits, flags), refuse to start exposed without `FORGE_ACCESS_TOKEN`. `logging_setup.py` with structlog and the redaction filter. FastAPI app factory with `/healthz`, `/readyz`, `/version`, the Host allow-list middleware, the `X-Forge-Request` + Origin check middleware, security headers, error handler with the single error shape.
**Files:** `config.py`, `logging_setup.py`, `errors.py`, `api/app.py`, `api/middleware.py`
**Done when:** startup fails with a clear message for unsafe configs; security tests 10 (local parts) pass; redaction unit tests pass.

## T03 - Database and migrations
**Depends on:** T02
**Build:** SQLAlchemy 2.0 async models for every table in `02-architecture.md` section 4, SQLite in WAL mode, Alembic setup and first migration, UUIDv7 helper, session management, retention helper.
**Files:** `db/`, `migrations/`
**Done when:** `alembic upgrade head` and `downgrade base` work on a clean database; model tests pass.

## T04 - Security primitives
**Depends on:** T02
**Build:** `core/security/`: `ssrf.py` (resolve + block ranges, connect-time re-check, redirect handling), `safe_yaml.py` (safe loader, alias/depth guard), `paths.py` (containment checks), `redact.py`, `unicode.py` (strip invisible/bidi, NFKC), identifier validation helper. Each with thorough unit tests.
**Files:** `core/security/*`
**Done when:** security tests 2, 5, 6 (unicode part), 7 (redaction unit part) and 9 (path helper) pass.

## T05 - Ingest
**Depends on:** T04
**Build:** `core/ingest/`: read from upload, pasted text or link with streaming size cap, timeout, content checks; detect JSON vs YAML; return raw text + metadata. URL fetch uses the SSRF guard. Reject URLs with credentials.
**Files:** `core/ingest/*`
**Done when:** ingest tests pass including oversize, wrong content type, redirect-to-private, and slow-server cases.

## T06 - Parse and validate
**Depends on:** T05
**Build:** `core/parse/`: safe load, detect Swagger 2.0 / 3.0 / 3.1 / 3.2, validate with the right validator (confirm the validator supports 3.2; if not, fall back to structural checks and record a warning), local `$ref` resolution with cycle detection and size/depth caps, remote refs off by default, readable errors with JSON-pointer locations.
**Files:** `core/parse/*`
**Done when:** golden tests over the samples pass; hostile specs (alias bomb, deep nesting, cycles) fail fast under the time limit (security test 4).

## T07 - Internal model (IR) and normalization
**Depends on:** T06
**Build:** `core/ir/models.py` (Pydantic models for API info, servers, security schemes, operations, parameters, bodies, responses), normalizers for Swagger 2.0 and OpenAPI 3.x into the IR, `schema_tools.py` (resolve `$ref`, merge `allOf`, handle `oneOf/anyOf/nullable`, depth cut, size cap, convert to plain JSON Schema). Stable `operation_key` generation.
**Files:** `core/ir/*`
**Done when:** the same logical API expressed as Swagger 2.0, 3.0, 3.1 and 3.2 normalizes to equivalent IR (tested); `operation_key`s are stable across re-parses.

## T08 - Tool mapping
**Depends on:** T07
**Build:** `core/mapping/`: naming rules and collision handling, description cleaning and caps, flat input schema building (parameters + body, flatten small bodies), annotations, auth mapping, safe default selection and presets, skipped-operation reasons. Output is a `ToolSet` data structure plus the `tools.json` document model with a JSON Schema for validating it.
**Files:** `core/mapping/*`
**Done when:** unit tests cover naming edge cases (unicode, long, reserved, duplicates), default selection (security test 12), and the manifest validates against its schema.

## T09 - Review engine
**Depends on:** T08
**Build:** `core/review/`: engine, all rules in `02-architecture.md` section 7 (including `SEC-006` for key-like strings), pattern list for instruction-like text with tests (positives and negatives), acknowledgement logic.
**Files:** `core/review/*`
**Done when:** each rule has passing and failing fixtures; `SEC-001/002` tests (security test 6) pass.

## T10 - Generated runtime library
**Depends on:** T08
**Build:** The static `runtime/` files from `02-architecture.md` section 8 inside `templates/server_project/runtime/`: config, auth (API key in header/query/cookie, bearer, basic, client-credentials with token cache), request builder (path encoding, query style/explode, headers, JSON/form bodies), httpx client (timeouts, safe-method retries with backoff and Retry-After, SSRF guard with `ALLOW_PRIVATE_TARGETS`), response shaping (truncation with note, error mapping, secret scrubbing), logging to stderr with redaction, per-tool and global rate limiting. Fully unit tested here with respx, as if it were a normal package.
**Files:** `templates/server_project/runtime/*`, `tests/unit/runtime/*`
**Done when:** runtime coverage is at least 90%; redaction and SSRF tests pass.

## T11 - Renderer and output checks
**Depends on:** T09, T10
**Build:** `core/render/`: Jinja2 environment (`StrictUndefined`), templates for `server.py`, `pyproject.toml`, `README.md`, `.env.example`, `Dockerfile`, generated tests; `tools.json` writer; `server.py` registers tools from the manifest using the SDK API verified in `docs/sdk-notes.md`, supports stdio and Streamable HTTP, enforces the bind/token/Host/Origin rules. `check_output.py`: `ast.parse` every file, forbidden-call scan, `ruff format` + lint, manifest schema validation. Deterministic output (sorted keys, fixed timestamps) so builds are reproducible.
**Files:** `core/render/*`, `templates/server_project/*`
**Done when:** security tests 1, 2, 3 pass; generating the same input twice gives byte-identical output; golden snapshot tests for the sample specs pass.

## T12 - Packaging and generation service
**Depends on:** T11, T03
**Build:** `core/render/package.py` (deterministic zip + sha256), `services/builds.py` (create build row, run pipeline in a worker with timeout, store artifacts under the data dir, record warnings), file tree and safe file read helpers, connection snippet generator. Check each target client's current config format in its official docs before writing snippets.
**Files:** `core/render/package.py`, `services/builds.py`, `services/review.py`
**Done when:** a build for each sample spec succeeds and is stored; download checksum matches; path traversal attempts fail (security test 9).

## T13 - Generated project end-to-end test
**Depends on:** T12
**Build:** An integration test that generates a project from a sample spec, creates a virtual environment, installs it, runs its own test suite, starts it over stdio, connects with the SDK client, lists tools, calls a read-only tool against a respx or local fake API, and asserts stdout stayed clean (security test 11). Also a Streamable HTTP start test including the non-loopback refusal and bad Host/Origin rejection.
**Files:** `tests/integration/test_generated_project.py`
**Done when:** the test passes in CI for all samples.

## T14 - Mock API
**Depends on:** T07
**Build:** `mock_api/`: build routes from the IR (path templates, methods), validate incoming requests against parameter/body schemas, generate responses from `example`/`examples` first, then from response schemas with deterministic seeded data (strings, formats, enums, arrays, nested objects), correct status codes and content types, simulated errors on request (`X-Mock-Status`). Runs as an in-process local HTTP server on a random loopback port, started and stopped per Playground session.
**Files:** `mock_api/*`
**Done when:** for each sample, every enabled operation returns a response that validates against its documented schema (tested by a script that walks all operations).

## T15 - Playground backend
**Depends on:** T13, T14
**Build:** `playground/`: session manager (limits, caps, timeouts), sandbox launcher (scrubbed env, temp dir, resource limits, process group kill), MCP client using the SDK over stdio, tool listing, tool call with timeout and size caps, trace recorder (every message with direction and timing, redacted, size-capped), server-sent events stream, cleanup on stop and shutdown. Targets: mock (starts mock API, sets base URL) and live (credentials in memory only). Flag `PLAYGROUND_ENABLED`.
**Files:** `playground/*`, `api/routes/playground.py`
**Done when:** security tests 7 (traces) and 8 pass; a mock session lists tools and runs a call with a visible trace; sessions clean up after crashes.

## T16 - Forge REST API
**Depends on:** T12, T15, T09
**Build:** All routes from `02-architecture.md` section 5 with schemas, selection saving and preservation across spec versions, spec diff (`core/diff.py`), presets, review and acknowledge, builds, files, download, connect snippets, samples, delete project with confirmation, rate limits, exposed-mode access-token login with session cookie and CSRF token. Generate OpenAPI types for the frontend.
**Files:** `api/routes/*`, `api/schemas/*`, `services/*`, `core/diff.py`
**Done when:** API tests cover every route including auth failures and validation errors; security test 10 fully passes; re-uploading a spec keeps matching operation choices.

## T17 - Command line
**Depends on:** T16
**Build:** `forge check <spec>`, `forge review <spec>`, `forge generate <spec> -o <dir> [--read-only | --select ... | --config file]`, `forge serve`, `forge samples`, `forge wipe`. Same core as the API. Exit codes: 0 ok, 1 invalid spec or blocking finding, 2 usage error. Output readable and also `--json` for pipelines.
**Files:** `cli/main.py`
**Done when:** CLI tests pass; `forge generate` output equals the API build output for the same input.

## T18 - Frontend foundation
**Depends on:** T16
**Build:** App shell, navigation, theme tokens from `04-frontend.md`, API client (header, errors, generated types), TanStack Query setup, mode banner, login screen (exposed mode), Home with samples, shared components (`EmptyState`, `ErrorState`, `ConfirmDialog`, `RiskBadge`, `MethodPill`, `CodeViewer`).
**Files:** `frontend/src/...`
**Done when:** you can open the app, see samples, and (in exposed mode) log in; CSP headers present; axe check shows no serious issues.

## T19 - New project and overview screens
**Depends on:** T18
**Build:** New project (upload, paste, link, sample), validation report with locations, project overview with stepper, spec version history, spec diff view.
**Done when:** every state is implemented; invalid and hostile files show clear errors without breaking the UI.

## T20 - Tools, settings and review screens
**Depends on:** T19
**Build:** Virtualized operation table with inline rename, switches, filters, presets, tool budget bar, description editor with agent-view preview; settings form; review screen with acknowledgements and the text diff for cleaned text.
**Done when:** a 5,000-operation spec stays responsive (measure and note in `docs/benchmarks.md`); default selection is read-only; enabling a write tool shows the confirmation.

## T21 - Builds and connect screens
**Depends on:** T20
**Build:** Generate action with progress, build list, file tree and code viewer, download, connect panel with snippets and env var list.
**Done when:** a full flow (sample, generate, browse files, download) works; downloaded archive checksum matches the displayed one.

## T22 - Playground screen
**Depends on:** T21
**Build:** Session controls, credential fields (memory only), tool list, schema form, run and result viewer, protocol trace with SSE, live-mode warnings and confirmation for non-read-only tools, session stop and cleanup.
**Done when:** the Playwright smoke flow passes: sample project, generate, start mock session, run a tool, see the trace; credentials never appear in storage, URLs or the query cache.

## T23 - Hardening, fuzzing and benchmarks
**Depends on:** T17, T22
**Build:** Run every test in `03-security.md` section 11 and fix gaps. Add hypothesis fuzz suites for names/descriptions/schemas. Collect a corpus of real public OpenAPI files (small, large, Swagger 2.0, 3.0, 3.1) as test fixtures or via a documented optional download script; run all of them through the pipeline and record pass/fail with reasons in `docs/compatibility.md`. Measure parse and generate time for a 5,000-operation synthetic spec and write real numbers to `docs/benchmarks.md`.
**Done when:** all tests pass in CI; both docs contain measured results only.

## T24 - Documentation and release packaging
**Depends on:** T23
**Build:** `README.md` (what it is, a clear "how it works" diagram, 5-minute quick start with the sample and the Playground, CLI usage, configuration table, security model, limits and trade-offs), `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, issue and PR templates, guides in `docs/guides/` (connect to a desktop AI app, use in CI, expose safely, write good API descriptions for agents), release notes `v0.1.0`, release workflow building the container image and the Python package. Screenshots only from the real running app.
**Done when:** a fresh clone reaches a working mock tool call following only the README in under 10 minutes.

## T25 (stretch) - TypeScript output target
**Depends on:** T24
**Build:** Only if everything above is green. Add a second renderer producing a TypeScript server using the current official TypeScript SDK v2 packages, following the same data/code separation (manifest + static runtime). Reuse the review and mapping code. Add the same end-to-end test. If this cannot be finished cleanly, do not ship a half version: document it as planned.
**Done when:** the generated TypeScript project installs, builds, lists tools and calls one against the mock; otherwise the ticket is closed as "not done" in `FINAL_REPORT.md`.

<!-- END FILE -->

<!-- FILE: docs/06-deployment.md -->
# 06 - Deployment

Reads: `02-architecture.md`, `03-security.md`.

## 1. Environments
| Environment | How | Notes |
|---|---|---|
| Local dev | `make dev` (backend with reload, frontend dev server) | Local mode, Playground on, sample specs available |
| Local use (recommended for most people) | `docker compose up` or `uvx mcp-forge serve` | Binds to 127.0.0.1 only |
| CI | GitHub Actions | Lint, types, tests (including integration with a virtual environment for the generated project), audits, image build |
| Shared server (optional) | Docker Compose behind HTTPS reverse proxy | Exposed mode: access token required; Playground off unless enabled |

Hardware: 1 vCPU and 1 GB RAM is enough for normal specs. Very large specs (thousands of operations) are better with 2 GB.

## 2. Environment variables (`.env.example` lists all, with no real values)
| Variable | Purpose | Default |
|---|---|---|
| `ENV` | `development` or `production` | `production` |
| `FORGE_MODE` | `local` or `exposed` | `local` |
| `FORGE_HOST` / `FORGE_PORT` | Bind address and port | `127.0.0.1` / `8080` |
| `FORGE_PUBLIC_HOST` | Extra allowed Host value when behind a proxy | empty |
| `FORGE_ACCESS_TOKEN` | Required when `FORGE_MODE=exposed` (long random value) | empty |
| `FORGE_DATA_DIR` | SQLite file, builds, temp | `./data` |
| `DATABASE_URL` | Defaults to a SQLite file in the data dir | derived |
| `MAX_SPEC_BYTES` | Spec size cap | 10 MB |
| `PIPELINE_TIMEOUT_S` | Parse/generate wall-clock limit | 30 |
| `PLAYGROUND_ENABLED` | Allow running generated servers | `true` in local, `false` in exposed |
| `PLAYGROUND_MAX_SESSIONS` | Concurrent sessions | 3 |
| `PLAYGROUND_IDLE_TIMEOUT_S` | Idle stop | 900 |
| `TRACE_RETENTION_DAYS` | Trace cleanup | 7 |
| `ALLOW_PRIVATE_SPEC_URLS` | Allow fetching specs from private addresses | `false` |
| `ALLOW_REMOTE_REFS` | Allow remote `$ref` resolution | `false` |
| `LOG_LEVEL` | Log level | `info` |

For generated projects, the variables are documented inside each generated `README.md` and `.env.example` (API credentials, `MCP_AUTH_TOKEN`, `ALLOW_PRIVATE_TARGETS`, limits).

## 3. First-time setup (local)
1. Install Docker, or install `uv`.
2. `git clone` the repository, copy `.env.example` to `.env` (defaults are safe for local use).
3. `docker compose up -d`, then open `http://127.0.0.1:8080`. Or `uvx mcp-forge serve` for the packaged version.
4. Click a sample API, press Generate, open the Playground, run a tool on the mock.

## 4. Setup on a shared server (exposed mode)
1. Generate a long random token (`openssl rand -base64 48`) and set `FORGE_MODE=exposed`, `FORGE_ACCESS_TOKEN`, `FORGE_PUBLIC_HOST`.
2. Run behind a reverse proxy with HTTPS (Caddy example in `docs/guides/expose-safely.md`). Do not publish the app port directly.
3. Leave `PLAYGROUND_ENABLED=false` unless you understand it runs generated servers on that machine.
4. Restrict network access (VPN or IP allow-list) as a second layer.

## 5. Data and migrations
- All data lives in `FORGE_DATA_DIR`: the SQLite database, build artifacts and temporary Playground folders.
- Migrations run automatically at start with Alembic (guarded by a lock). Every migration has an upgrade and a downgrade, tested in CI on a clean database and on one with sample data.
- Destructive schema changes ship in two releases (stop using, then remove).

## 6. Backup and restore
- Stop the app (or use SQLite's online backup), copy `FORGE_DATA_DIR`. That is the full backup. Specs and builds are reproducible from the stored spec text.
- Restore: stop the app, replace the folder, start. Migrations bring the schema forward.

## 7. Updating and rollback
1. `git pull` and `docker compose pull` (or rebuild), then `docker compose up -d`. Read the release notes first.
2. Take a backup of the data folder before a minor or major update.
3. Rollback: set the previous image tag and restore the backup if the release included a migration (the release notes state if downgrade is safe).
4. Old builds stay valid: each generated project is standalone and records the generator version that made it.

## 8. Monitoring
- `GET /healthz` (alive) and `GET /readyz` (database reachable, data dir writable). Compose healthchecks use them.
- Structured JSON logs to stdout: request ids, timings, counts, error codes, never spec text or credentials.
- Useful signals to watch: pipeline duration, failed builds ratio, active Playground sessions, stuck processes (should be zero after session end), disk usage of the data folder.
- Nightly cleanup job removes expired traces and orphan temp folders.

## 9. Release process
- Semantic versioning, tags `vX.Y.Z`.
- GitHub Actions on tag: run all checks, build and push the container image, build the Python package, create the release with notes. Package publishing to the Python registry uses the registry's trusted publishing flow (no long-lived tokens in secrets).
- Each release checks: tests green, audits clean at high severity, `docs/compatibility.md` and `docs/benchmarks.md` regenerated from real runs.

## 10. Optional: publishing a generated server
Not done by Forge. Each generated project ships with a Dockerfile and a README section showing how to run it, containerize it, and (optionally) publish it. Keep API credentials out of images: pass them at run time.

<!-- END FILE -->
