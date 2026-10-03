"""Jinja2 templating environment setup with StrictUndefined and safe filters."""

import json
from pathlib import Path
from typing import Any

import jinja2

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates" / "server_project"


def to_json_filter(value: Any, indent: int = 2) -> str:
    """Serialize value to deterministic formatted JSON."""
    return json.dumps(value, indent=indent, sort_keys=True)


def create_jinja_env() -> jinja2.Environment:
    """Create a configured Jinja2 environment with strict variable undefined checks."""
    loader = jinja2.FileSystemLoader(str(TEMPLATES_DIR))
    env = jinja2.Environment(
        loader=loader,
        undefined=jinja2.StrictUndefined,
        autoescape=False,  # noqa: S701 - Python code generation, not HTML/web template
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.filters["to_json"] = to_json_filter
    return env
