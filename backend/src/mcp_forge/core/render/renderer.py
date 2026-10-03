"""Project renderer orchestrator: renders all templates, writes manifest, copies runtime, and validates AST."""

from pathlib import Path
from typing import Any

from mcp_forge.core.mapping.manifest import ManifestDoc
from mcp_forge.core.render.check_output import check_generated_project
from mcp_forge.core.render.jinja_env import create_jinja_env
from mcp_forge.core.render.writer import (
    copy_runtime_files,
    render_template_to_file,
    write_manifest_json,
)


def render_project(
    manifest: ManifestDoc,
    output_dir: Path,
    slug: str = "api",
) -> Path:
    """Render a complete, ready-to-run MCP server project directory from ManifestDoc.

    Enforces deterministic output, forbidden call AST security checks, and schema validation.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    env = create_jinja_env()

    # Context for template rendering
    required_env_vars: list[str] = []
    for _scheme_name, scheme_info in manifest.auth.items():
        if isinstance(scheme_info, dict):
            required_env_vars.extend(scheme_info.get("required_env_vars", []))

    context: dict[str, Any] = {
        "title": manifest.info.title,
        "version": manifest.info.version,
        "slug": slug,
        "base_url": manifest.info.base_url,
        "required_env_vars": sorted(set(required_env_vars)),
        "tools": [t.model_dump() for t in manifest.tools],
    }

    # 1. Write tools.json
    write_manifest_json(manifest, output_dir / "tools.json")

    # 2. Render templates
    render_template_to_file(env, "server.py.jinja", context, output_dir / "server.py")
    render_template_to_file(env, "pyproject.toml.jinja", context, output_dir / "pyproject.toml")
    render_template_to_file(env, "README.md.jinja", context, output_dir / "README.md")
    render_template_to_file(env, ".env.example.jinja", context, output_dir / ".env.example")
    render_template_to_file(env, "Dockerfile.jinja", context, output_dir / "Dockerfile")

    # 3. Render tests
    render_template_to_file(
        env, "tests/test_manifest.py.jinja", context, output_dir / "tests" / "test_manifest.py"
    )
    render_template_to_file(
        env, "tests/test_server.py.jinja", context, output_dir / "tests" / "test_server.py"
    )
    render_template_to_file(
        env, "tests/test_runtime.py.jinja", context, output_dir / "tests" / "test_runtime.py"
    )

    # 4. Copy static runtime files
    copy_runtime_files(output_dir / "runtime")

    # 5. Security & AST output validation
    check_generated_project(output_dir)

    return output_dir
