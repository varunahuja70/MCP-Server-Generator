# MCP Forge Progress Log

| Ticket | Status | Result / Notes |
|---|---|---|
| T01 | COMPLETED | Project setup done. Repo skeleton, backend with uv + MCP Python SDK v2 (2.3.0) + FastAPI + Typer CLI, frontend with Next.js 16 + React 19 + Tailwind v4 + Vitest. Lint, types, tests all green. `docs/versions.lock.md` and `docs/sdk-notes.md` created. |
| T02 | COMPLETED | Config, logging and app shell done. Strict exposed/local config validation, structlog redaction filter, FastAPI factory with single error format, security headers, Host allowlist, and CSRF/X-Forge-Request middleware. Security test 10 (local parts) and redaction tests pass. |
| T03 | COMPLETED | Database and migrations done. SQLAlchemy 2.0 async models for all 9 entities from spec, monotonic UUIDv7 generator, SQLite WAL mode, Alembic async migrations with upgrade/downgrade, and trace retention purge. All model lifecycle tests pass. |
| T04 | COMPLETED | Security primitives done. SSRF validator and safe fetcher with redirect re-validation, safe YAML loader with alias bomb and depth protection, filesystem path containment guard, unicode cleaner stripping invisible/bidi/control chars, identifier gate, and secret redaction. Security tests 2, 5, 6, 7, 9 all pass. |
| T05 | COMPLETED | Ingest done. Ingest from uploaded bytes, text paste, and links with streaming size limit (10MB), JSON/YAML format detection, SHA256 hashing, UTF-8/BOM handling, and SSRF guard on links. Ingest unit tests pass. |
| T06 | COMPLETED | Parse and validate done. Safe loading, Swagger 2.0 / OAS 3.0 / 3.1 / 3.2 detection, validation against official OpenAPI schema with JSON pointer locations, local $ref resolution with cycle cut and depth limits, remote refs blocked by default. Bundled samples (bookshop, tasks, legacy swagger, hostile specs). Golden tests and Security test 4 (alias bomb, deep nesting, cycles) all pass under limits. |
| T07 | COMPLETED | Internal model (IR) and normalization done. Pydantic v2 IR models (IRApi, IROperation, IRParameter, IRRequestBody, IRResponse, IRSecurityScheme, IRServer). Normalizers for Swagger 2.0 and OpenAPI 3.0/3.1/3.2 into IR. Schema tools with local ref resolution, allOf merging, nullable normalization, depth cut and AST size capping. Tested equivalent IR across Swagger 2.0, 3.0, 3.1 and 3.2, with stable operation keys across re-parses. |
| T08 | COMPLETED | Tool mapping done. Naming engine enforcing `^[a-z][a-z0-9_]{0,63}$`, reserved words/runtime shadowing resolution, collision disambiguation. Description cleaner with NFKC + invisible/bidi character stripping, markdown flattening, length capping. Input schema builder for flat schemas with parameter locations and small-body flattening (<=8 props). Annotations for read-only, destructive, idempotent, open-world. Auth mapping to env vars. Safe default selection (Security test 12: read-only on, writes off) and presets. ManifestDoc model and `tools.json` JSON Schema validation. |



