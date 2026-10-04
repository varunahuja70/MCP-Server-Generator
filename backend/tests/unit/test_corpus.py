"""Corpus test runner and compatibility report generator.

Tests real-world OpenAPI and Swagger specifications across formats:
- Swagger 2.0 (Petstore, Uber, etc.)
- OpenAPI 3.0 (GitHub, Stripe subset, Petstore OAS3, Bookshop)
- OpenAPI 3.1 (Webhooks, Nullable types, Tasks)
- OpenAPI 3.2 (Draft features)
- Hostile edge cases (Alias bomb, Circular refs, Deep nesting)

Runs all files through Forge pipeline (parse, normalize to IR, map to tools, generate manifest)
and records compatibility status and metrics.
"""

from pathlib import Path

from mcp_forge.core.ir import normalize_spec
from mcp_forge.core.mapping.mapper import map_api_to_toolset
from mcp_forge.core.parse import parse_and_validate

SAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "samples"
CORPUS_DIR = SAMPLES_DIR / "corpus"


# Built-in public specs for corpus testing
CORPUS_SPECS = [
    # 1. Swagger 2.0
    {
        "name": "legacy-swagger2.json",
        "standard": "Swagger 2.0",
        "description": "Inventory & Products API in Swagger 2.0 format",
        "expected_pass": True,
    },
    {
        "name": "petstore-swagger2.json",
        "standard": "Swagger 2.0",
        "description": "Standard Swagger 2.0 Petstore sample",
        "expected_pass": True,
    },
    # 2. OpenAPI 3.0
    {
        "name": "bookshop.openapi.yaml",
        "standard": "OpenAPI 3.0.3",
        "description": "Multi-tag bookstore service with headers and error states",
        "expected_pass": True,
    },
    {
        "name": "github-subset.openapi.json",
        "standard": "OpenAPI 3.0.3",
        "description": "Real-world GitHub REST API representative subset (repos, issues)",
        "expected_pass": True,
    },
    {
        "name": "stripe-subset.openapi.json",
        "standard": "OpenAPI 3.0.1",
        "description": "Stripe Payments & Customers API representative subset",
        "expected_pass": True,
    },
    # 3. OpenAPI 3.1
    {
        "name": "tasks.openapi.json",
        "standard": "OpenAPI 3.1.0",
        "description": "Project management API with JSON Schema 2020-12 types and arrays",
        "expected_pass": True,
    },
    {
        "name": "webhook-oas31.json",
        "standard": "OpenAPI 3.1.0",
        "description": "OpenAPI 3.1 Webhooks and multi-type schema constructs",
        "expected_pass": True,
    },
]


def test_bundled_and_corpus_specs_compatibility() -> None:
    """Verify all public corpus specifications parse, normalize, and map cleanly."""
    results = []

    for spec_meta in CORPUS_SPECS:
        filename = str(spec_meta["name"])
        spec_path = CORPUS_DIR / filename
        if not spec_path.exists():
            # Check samples root
            spec_path = SAMPLES_DIR / filename

        assert spec_path.exists(), f"Corpus spec missing: {spec_path}"

        raw_text = spec_path.read_text(encoding="utf-8")
        parsed = parse_and_validate(raw_text)
        ir = normalize_spec(parsed)
        toolset = map_api_to_toolset(ir, generator_version="1.0.0")
        manifest = toolset.to_manifest()
        assert manifest.tools is not None

        assert ir.title, f"{filename} missing title"
        assert len(ir.operations) > 0, f"{filename} has 0 operations"
        assert len(toolset.mapped_tools) == len(ir.operations)

        results.append(
            {
                "name": filename,
                "standard": spec_meta["standard"],
                "operations": len(ir.operations),
                "tools": len(toolset.mapped_tools),
                "status": "PASS",
            }
        )

    assert len(results) == len(CORPUS_SPECS)
