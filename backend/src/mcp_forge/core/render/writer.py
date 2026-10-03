"""Project writing helpers: deterministic manifest writer, runtime copier, and template rendering."""

import json
import shutil
from pathlib import Path
from typing import Any

import jinja2

from mcp_forge.core.mapping.manifest import ManifestDoc

RUNTIME_SOURCE_DIR = (
    Path(__file__).resolve().parent.parent.parent / "templates" / "server_project" / "runtime"
)


def write_manifest_json(manifest: ManifestDoc, target_path: Path) -> None:
    """Write tools.json with deterministic key ordering and 2-space indentation."""
    data = manifest.model_dump()
    json_bytes = json.dumps(data, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    target_path.write_bytes(json_bytes)


def copy_runtime_files(target_runtime_dir: Path) -> None:
    """Copy static runtime library files to the generated project directory."""
    target_runtime_dir.mkdir(parents=True, exist_ok=True)
    for py_file in RUNTIME_SOURCE_DIR.glob("*.py"):
        shutil.copy2(py_file, target_runtime_dir / py_file.name)


def render_template_to_file(
    env: jinja2.Environment,
    template_name: str,
    context: dict[str, Any],
    target_path: Path,
) -> None:
    """Render a Jinja2 template and write result deterministically to disk."""
    template = env.get_template(template_name)
    rendered = template.render(**context)
    # Ensure trailing newline
    if not rendered.endswith("\n"):
        rendered += "\n"
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(rendered, encoding="utf-8")
