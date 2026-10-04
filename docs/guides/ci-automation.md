# Using MCP Forge in CI/CD Pipelines

MCP Forge includes a standalone Typer CLI (`forge`) designed to integrate smoothly into continuous integration pipelines (GitHub Actions, GitLab CI, Jenkins) for automated validation, security linting, and server code generation.

---

## 1. Validating OpenAPI Changes on Pull Requests

Ensure that any changes to OpenAPI or Swagger specifications conform to strict standards and do not introduce breaking syntax errors.

```yaml
# .github/workflows/validate-spec.yml
name: Validate OpenAPI Spec

on:
  pull_request:
    paths:
      - 'openapi/**'

jobs:
  check-spec:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
        with:
          version: "latest"

      - name: Install MCP Forge
        run: uv pip install --system mcp-forge

      - name: Run Forge Check
        run: forge check openapi/service.yaml
```

---

## 2. Automated Security and Quality Review

Enforce security boundaries (detecting prompt injection patterns, secret leakage, or accidental exposure of mutating write tools):

```bash
# Run security review with JSON output for automated reporting
forge review openapi/service.yaml --json > review-results.json
```
If blocking findings (`SEC-001`, `SEC-002`, `SEC-004`) are encountered, `forge review` exits with code `1`, causing the CI pipeline step to fail automatically.

---

## 3. Automated Server Generation and Artifact Archival

Automatically generate your ready-to-run MCP server project whenever an API specification is tagged or merged to `main`:

```bash
# Generate server with read-only tools enabled
forge generate openapi/service.yaml -o ./artifacts/mcp-server --read-only

# Verify the generated server's internal test suite
cd ./artifacts/mcp-server
python -m pytest tests/
```
