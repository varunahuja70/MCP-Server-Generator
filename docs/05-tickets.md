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
