"""Benchmark and stress test for 5,000-operation synthetic OpenAPI specification.

Generates a valid 5,000-operation OpenAPI 3.0 specification, measures:
1. Parse and validation time
2. IR normalization time
3. Tool mapping and manifest generation time
4. Template rendering time
5. Packaging (ZIP + SHA256) time

Outputs measured real performance metrics.
"""

import json
import time
from pathlib import Path
from typing import Any

from mcp_forge.core.ir import normalize_spec
from mcp_forge.core.mapping.mapper import map_api_to_toolset
from mcp_forge.core.parse import parse_and_validate
from mcp_forge.core.render.package import create_deterministic_zip
from mcp_forge.core.render.renderer import render_project


def generate_synthetic_spec(op_count: int = 5000) -> str:
    """Generate a synthetic valid OpenAPI 3.0.3 specification with N operations."""
    paths: dict[str, Any] = {}

    for i in range(op_count):
        resource_id = i // 5
        sub_op = i % 5

        path = f"/api/v1/resource_{resource_id}"
        if sub_op == 0:
            method = "get"
            op_id = f"listResource_{resource_id}"
            summary = f"List resource items {resource_id}"
        elif sub_op == 1:
            method = "post"
            op_id = f"createResource_{resource_id}"
            summary = f"Create resource item {resource_id}"
        elif sub_op == 2:
            path = f"{path}/{{item_id}}"
            method = "get"
            op_id = f"getResource_{resource_id}"
            summary = f"Get resource item {resource_id}"
        elif sub_op == 3:
            path = f"{path}/{{item_id}}"
            method = "put"
            op_id = f"updateResource_{resource_id}"
            summary = f"Update resource item {resource_id}"
        else:
            path = f"{path}/{{item_id}}"
            method = "delete"
            op_id = f"deleteResource_{resource_id}"
            summary = f"Delete resource item {resource_id}"

        if path not in paths:
            paths[path] = {}

        operation_def: dict[str, Any] = {
            "summary": summary,
            "operationId": op_id,
            "responses": {
                "200": {
                    "description": "Successful operation",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "status": {"type": "string"},
                                },
                            }
                        }
                    },
                }
            },
        }

        if "{item_id}" in path:
            operation_def["parameters"] = [
                {
                    "name": "item_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "integer"},
                }
            ]

        paths[path][method] = operation_def

    spec_dict = {
        "openapi": "3.0.3",
        "info": {
            "title": "Synthetic 5000-Operation Benchmark API",
            "version": "1.0.0",
            "description": "Synthetic API benchmark specification containing 5000 distinct operations.",
        },
        "servers": [{"url": "https://api.benchmark.example.com"}],
        "paths": paths,
    }

    return json.dumps(spec_dict)


def test_benchmark_synthetic_5000_operations(tmp_path: Path) -> None:
    """Run measured benchmark on 5,000 operations synthetic spec."""
    # 1. Spec generation
    t0 = time.perf_counter()
    raw_spec = generate_synthetic_spec(5000)
    t_gen_spec = time.perf_counter() - t0

    # 2. Parse & Validate
    t0 = time.perf_counter()
    parsed = parse_and_validate(raw_spec)
    t_parse = time.perf_counter() - t0

    # 3. IR Normalization
    t0 = time.perf_counter()
    ir = normalize_spec(parsed)
    t_ir = time.perf_counter() - t0

    assert len(ir.operations) == 5000

    # 4. Tool Mapping & Manifest building
    t0 = time.perf_counter()
    toolset = map_api_to_toolset(ir, generator_version="1.0.0")
    manifest = toolset.to_manifest()
    t_mapping = time.perf_counter() - t0

    # 5. Project Rendering
    out_dir = tmp_path / "bench_server"
    t0 = time.perf_counter()
    render_project(manifest, out_dir, slug="bench_server")
    t_render = time.perf_counter() - t0

    # 6. Packaging ZIP & SHA256
    zip_path = tmp_path / "bench_server.zip"
    t0 = time.perf_counter()
    _, sha256_hash = create_deterministic_zip(out_dir, zip_path)
    t_package = time.perf_counter() - t0

    total_pipeline = t_parse + t_ir + t_mapping + t_render + t_package

    print("\n--- 5,000 OPERATIONS BENCHMARK RESULTS ---")
    print(f"Spec Generation:   {t_gen_spec:.4f}s ({len(raw_spec) / 1024 / 1024:.2f} MB)")
    print(f"Parse & Validate:  {t_parse:.4f}s")
    print(f"IR Normalization:  {t_ir:.4f}s")
    print(f"Tool Mapping:      {t_mapping:.4f}s")
    print(f"Project Rendering: {t_render:.4f}s")
    print(
        f"ZIP & Packaging:   {t_package:.4f}s ({zip_path.stat().st_size / 1024:.2f} KB, sha256={sha256_hash[:16]}...)"
    )
    print(f"Total Pipeline:    {total_pipeline:.4f}s")
    print("-------------------------------------------\n")

    # Sanity checks
    assert (out_dir / "tools.json").exists()
    assert (out_dir / "server.py").exists()
    assert total_pipeline < 120.0, f"Pipeline took too long: {total_pipeline}s"
