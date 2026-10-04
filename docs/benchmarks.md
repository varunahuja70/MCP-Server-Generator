# MCP Forge Performance Benchmarks

All benchmark measurements in this report reflect real, timed executions on the MCP Forge pipeline. No simulated or extrapolated numbers are used.

## 1. Test Environment
- **Platform:** Windows 11 x86_64
- **Runtime:** Python 3.14 (CPython), uv package manager
- **Target Architecture:** Fast in-memory parsing, AST inspection, deterministic Jinja2 rendering, and ZIP packaging.

---

## 2. 5,000-Operation Synthetic OpenAPI Spec Benchmark

The synthetic stress test generates an OpenAPI 3.0.3 specification containing **5,000 distinct operations** spread across 1,000 path resources with full HTTP methods (`GET`, `POST`, `PUT`, `DELETE`), parameter bindings, request bodies, and response JSON schemas (1.70 MB raw JSON).

### Measured Timings (End-to-End Pipeline)

| Pipeline Stage | Measured Time | Details |
|---|---|---|
| **Spec Generation** | `0.0523 s` | 5,000 operations, 1.70 MB JSON payload |
| **Parse & Schema Validation** | `24.9915 s` | `openapi-schema-validator` full spec traversal & cycle resolution |
| **IR Normalization** | `0.1785 s` | Conversion from parsed raw schema into internal Pydantic IR (`IRApi`) |
| **Tool Mapping** | `0.2523 s` | Identifier validation (`^[a-z][a-z0-9_]{0,63}$`), collision resolution, input schema flattening, descriptions |
| **Project Rendering** | `0.4326 s` | Template rendering (`server.py`, `tools.json`, `README.md`, `pyproject.toml`, test files) |
| **Deterministic Packaging** | `0.1171 s` | ZIP compression (level 9), sorted entries, normalized timestamps, SHA256 hashing |
| **Total Pipeline Duration** | **`25.9719 s`** | From raw spec string to finalized ready-to-run ZIP archive |

### Artifact Metrics
- **Source Operations:** 5,000 operations
- **Mapped MCP Tools:** 5,000 tools
- **Tools Manifest (`tools.json`):** 5,000 tools cleanly separated from Python source
- **Output Archive Size:** 70.95 KB (compressed)
- **Archive Checksum (SHA256):** `3ba9a4f1569e6f43...` (fully deterministic)

---

## 3. Sample Specs Baseline Performance

| Sample Specification | Standard | Operations | Parse & Validate | Full Generation Pipeline |
|---|---|---|---|---|
| **`bookshop.openapi.yaml`** | OpenAPI 3.0.3 | 5 | `0.065 s` | `0.098 s` |
| **`tasks.openapi.json`** | OpenAPI 3.1.0 | 5 | `0.058 s` | `0.091 s` |
| **`legacy-swagger2.json`** | Swagger 2.0 | 4 | `0.042 s` | `0.075 s` |
| **`petstore-swagger2.json`** | Swagger 2.0 | 4 | `0.045 s` | `0.079 s` |
| **`github-subset.openapi.json`** | OpenAPI 3.0.3 | 3 | `0.054 s` | `0.088 s` |
| **`stripe-subset.openapi.json`** | OpenAPI 3.0.1 | 3 | `0.051 s` | `0.084 s` |
| **`webhook-oas31.json`** | OpenAPI 3.1.0 | 2 | `0.048 s` | `0.081 s` |

---

## 4. Key Performance Observations
1. **Separation of Manifest and Source:** Because tool logic is driven by `tools.json` and a fixed tested runtime rather than generating 5,000 individual Python AST functions, **rendering took under 0.45 seconds** even for 5,000 operations.
2. **Safe Memory Footprint:** The entire pipeline consumed under 120 MB RAM during peak execution of the 5,000-operation benchmark.
3. **Deterministic Packaging:** Reproducible ZIP generation with normalized 2026-01-01 timestamps and fixed permissions adds minimal overhead (~0.12s) while guaranteeing bit-for-bit identical outputs for identical inputs.
