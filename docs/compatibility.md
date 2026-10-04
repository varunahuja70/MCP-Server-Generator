# MCP Forge OpenAPI / Swagger Compatibility Matrix

This document records the verified compatibility of MCP Forge with real-world OpenAPI and Swagger specifications across different standards, schema dialects, and architectural designs.

All entries are tested through the automated test suite in `tests/unit/test_corpus.py` and `tests/unit/test_parse.py`.

---

## 1. Supported Specification Standards

| Standard | Status | Parser & Validator | IR Normalizer | Notes |
|---|---|---|---|---|
| **Swagger 2.0** | ✅ **Full Support** | `swagger-2.0` schema validation | `normalize_swagger2.py` | Full support for definitions, parameters, produces/consumes, and basePath. |
| **OpenAPI 3.0.x** (3.0.0 - 3.0.4) | ✅ **Full Support** | `openapi-3.0` official schema | `normalize_oas3.py` | Full support for requestBody, components/schemas, servers, parameters in query/path/header/cookie. |
| **OpenAPI 3.1.x** (3.1.0 - 3.1.1) | ✅ **Full Support** | `openapi-3.1` official schema | `normalize_oas3.py` | Full support for JSON Schema 2020-12, multi-type arrays (`type: ["string", "null"]`), and webhooks. |
| **OpenAPI 3.2.x** (3.2.0 draft) | ✅ **Full Support** | `openapi-3.2` official schema | `normalize_oas3.py` | Seamless forward compatibility with 3.2 draft specifications. |

---

## 2. Public Spec Corpus Test Results

| Specification File | Standard | Domain / API Type | Operations Mapped | Status | Verified Features |
|---|---|---|---|---|---|
| **`bookshop.openapi.yaml`** | OpenAPI 3.0.3 | E-Commerce / Bookstore | 5 | ✅ **PASS** | Multi-tag, header parameters, error schema models, YAML syntax. |
| **`tasks.openapi.json`** | OpenAPI 3.1.0 | Project Management | 5 | ✅ **PASS** | JSON Schema 2020-12 types, nullable properties, nested arrays. |
| **`legacy-swagger2.json`** | Swagger 2.0 | Inventory & Products | 4 | ✅ **PASS** | Swagger 2.0 definitions, basePath routing, body parameter flattening. |
| **`petstore-swagger2.json`** | Swagger 2.0 | Sample Petstore | 4 | ✅ **PASS** | Standard Swagger 2.0 schema, enum query parameters, multipart consumes. |
| **`github-subset.openapi.json`** | OpenAPI 3.0.3 | Developer Platforms / GitHub | 3 | ✅ **PASS** | Real-world REST naming patterns (`/repos/{owner}/{repo}/issues`), nullable fields. |
| **`stripe-subset.openapi.json`** | OpenAPI 3.0.1 | Fintech & Payments / Stripe | 3 | ✅ **PASS** | Form-encoded body schemas (`application/x-www-form-urlencoded`), object wrappers. |
| **`webhook-oas31.json`** | OpenAPI 3.1.0 | Event Subscriptions & Webhooks | 2 | ✅ **PASS** | OpenAPI 3.1 top-level `webhooks` object, union types (`["string", "integer"]`). |

---

## 3. Hostile & Edge Case Specifications

MCP Forge includes defensive fixtures in `samples/hostile/` tested under `tests/security/`:

| Fixture File | Threat Vector | Defense Mechanism | Result | Reason / Action |
|---|---|---|---|---|
| **`alias-bomb.yaml`** | Billion laughs YAML entity expansion | `SafeYAMLLoader` with alias count cap (100) | 🛡️ **BLOCKED** | Rejected with `SecurityViolationError`: Alias expansion limit exceeded. |
| **`circular-refs.yaml`** | Self-referencing circular `$ref` graph | Cycle detection set in `resolve_refs` | 🛡️ **BLOCKED** | Cycle safely severed or failed fast with depth limit. |
| **`deep-nesting.yaml`** | 100+ nested JSON objects / arrays | Maximum depth cut (default 20 levels) | 🛡️ **BLOCKED** | Truncated to avoid stack overflows. |
| **`hostile-names.yaml`** | Python injection in operation IDs | Regex identifier gate `^[a-z][a-z0-9_]{0,63}$` | 🛡️ **SANITIZED** | Names sanitized into safe ASCII identifiers; arbitrary text kept in JSON only. |

---

## 4. Known Boundaries & Non-Goals

1. **Remote `$ref` Resolution:** By default, remote HTTP references are disabled to eliminate SSRF attacks. Can be enabled on a per-project basis with strict SSRF validation.
2. **Streaming Binary Payloads:** OpenAPI operations returning raw binary streams (e.g. video streaming, massive file downloads) are capped by the runtime response size limiter.
3. **Complex XML Payloads:** Focus is on JSON, form-encoded, and text payloads; XML is passed as raw string.
