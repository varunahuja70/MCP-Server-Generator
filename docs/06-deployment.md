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
