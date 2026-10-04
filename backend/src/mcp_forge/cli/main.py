"""MCP Forge Command Line Interface."""

import asyncio
import json
import re
import shutil
from pathlib import Path
from typing import Any

import typer

from mcp_forge.api.app import create_app
from mcp_forge.config import Settings
from mcp_forge.core.ingest.sources import ingest_from_url
from mcp_forge.core.ir import normalize_spec
from mcp_forge.core.mapping.mapper import map_api_to_toolset
from mcp_forge.core.mapping.selection import determine_default_selection, is_read_only_method
from mcp_forge.core.parse import parse_and_validate
from mcp_forge.core.render.renderer import render_project
from mcp_forge.core.review.engine import review_api
from mcp_forge.errors import ForgeError
from mcp_forge.version import __version__

app = typer.Typer(
    name="forge",
    help="MCP Forge - Generate production-ready MCP servers from OpenAPI specs.",
    no_args_is_help=True,
)

SAMPLES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "samples"


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"mcp-forge version {__version__}")
        raise typer.Exit()


def _load_spec_text(spec_arg: str) -> tuple[str, str]:
    """Load spec text from local file path or URL."""
    spec_path = Path(spec_arg)
    if spec_path.exists() and spec_path.is_file():
        raw_text = spec_path.read_text(encoding="utf-8")
        return raw_text, spec_path.name

    if spec_arg.startswith("http://") or spec_arg.startswith("https://"):
        res = asyncio.run(ingest_from_url(spec_arg, allow_private=False))
        return res.raw_text, spec_arg

    # Check in samples directory
    sample_candidate = SAMPLES_DIR / spec_arg
    if sample_candidate.exists() and sample_candidate.is_file():
        raw_text = sample_candidate.read_text(encoding="utf-8")
        return raw_text, sample_candidate.name

    raise FileNotFoundError(f"Spec file or URL '{spec_arg}' not found.")


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """MCP Forge CLI root callback."""


@app.command()
def check(
    spec: str = typer.Argument(..., help="Path or URL to OpenAPI specification"),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON"),
) -> None:
    """Validate an OpenAPI specification."""
    try:
        raw_text, ref_name = _load_spec_text(spec)
    except Exception as e:
        if json_output:
            typer.echo(json.dumps({"error": str(e), "valid": False}))
        else:
            typer.secho(f"Error loading spec: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from None

    try:
        parsed = parse_and_validate(raw_text)
        ir = normalize_spec(parsed)

        result = {
            "valid": True,
            "title": ir.title,
            "version": ir.version,
            "kind": parsed.kind,
            "operation_count": len(ir.operations),
        }

        if json_output:
            typer.echo(json.dumps(result, indent=2))
        else:
            typer.secho(f"[OK] Specification '{ref_name}' is valid.", fg=typer.colors.GREEN)
            typer.echo(f"  Title: {ir.title} (v{ir.version})")
            typer.echo(f"  Format: {parsed.kind}")
            typer.echo(f"  Operations: {len(ir.operations)}")
        return

    except typer.Exit:
        raise
    except ForgeError as fe:
        if json_output:
            typer.echo(json.dumps({"valid": False, "error": fe.to_dict()["error"]}))
        else:
            typer.secho(
                f"[ERROR] Specification is invalid: {fe.message}", fg=typer.colors.RED, err=True
            )
        raise typer.Exit(code=1) from None
    except Exception as e:
        if json_output:
            typer.echo(json.dumps({"valid": False, "error": str(e)}))
        else:
            typer.secho(f"[ERROR] Specification error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from None


@app.command()
def review(
    spec: str = typer.Argument(..., help="Path or URL to OpenAPI specification"),
    json_output: bool = typer.Option(False, "--json", help="Output findings as JSON"),
) -> None:
    """Review an OpenAPI specification for security and quality."""
    try:
        raw_text, ref_name = _load_spec_text(spec)
    except Exception as e:
        if json_output:
            typer.echo(json.dumps({"error": str(e)}))
        else:
            typer.secho(f"Error loading spec: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from None

    try:
        parsed = parse_and_validate(raw_text)
        ir = normalize_spec(parsed)
        toolset = map_api_to_toolset(ir=ir, generator_version=__version__)
        report = review_api(
            ir=ir, toolset=toolset, raw_text=raw_text, raw_spec_dict=parsed.raw_dict
        )

        findings_data = [
            {
                "code": f.code,
                "severity": f.severity,
                "message": f.message,
                "operation_key": f.operation_key,
                "suggestion": f.suggestion,
            }
            for f in report.findings
        ]

        if json_output:
            typer.echo(
                json.dumps(
                    {
                        "has_blocking_errors": report.has_blocking_errors,
                        "error_count": report.error_count,
                        "warning_count": report.warning_count,
                        "info_count": report.info_count,
                        "findings": findings_data,
                    },
                    indent=2,
                )
            )
        else:
            typer.echo(f"Review for '{ref_name}':")
            typer.echo(
                f"Findings: {report.error_count} error(s), {report.warning_count} warning(s), {report.info_count} info"
            )
            for f in report.findings:
                color = (
                    typer.colors.RED
                    if f.severity == "error"
                    else (typer.colors.YELLOW if f.severity == "warning" else typer.colors.BLUE)
                )
                typer.secho(f"  [{f.code}] {f.severity.upper()}: {f.message}", fg=color)
                if f.suggestion:
                    typer.echo(f"    Suggestion: {f.suggestion}")

        if report.has_blocking_errors:
            raise typer.Exit(code=1)
        return

    except typer.Exit:
        raise
    except ForgeError as fe:
        if json_output:
            typer.echo(json.dumps({"error": fe.to_dict()["error"]}))
        else:
            typer.secho(f"Review error: {fe.message}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from None


@app.command()
def generate(
    spec: str = typer.Argument(..., help="Path or URL to OpenAPI specification"),
    output: Path = typer.Option(
        ..., "-o", "--output", help="Output directory for generated server"
    ),
    read_only: bool = typer.Option(
        False, "--read-only", help="Enable only safe read-only operations"
    ),
    select_ops: list[str] | None = typer.Option(
        None, "--select", help="Explicit operation keys or tool names to enable"
    ),
    config: Path | None = typer.Option(None, "--config", help="JSON/YAML configuration file"),
    json_output: bool = typer.Option(False, "--json", help="Output result as JSON"),
) -> None:
    """Generate an MCP server project from an OpenAPI specification."""
    try:
        raw_text, ref_name = _load_spec_text(spec)
    except Exception as e:
        if json_output:
            typer.echo(json.dumps({"error": str(e)}))
        else:
            typer.secho(f"Error loading spec: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from None

    try:
        parsed = parse_and_validate(raw_text)
        ir = normalize_spec(parsed)

        # Parse config file if provided
        cfg_data: dict[str, Any] = {}
        if config and config.exists():
            cfg_data = json.loads(config.read_text(encoding="utf-8"))

        tool_prefix = cfg_data.get("tool_prefix")
        base_url = cfg_data.get("base_url")

        # Determine enabled operations
        enabled_overrides: dict[str, bool] = {}
        selected_set = set(select_ops) if select_ops else None

        for op in ir.operations:
            if selected_set is not None:
                # Explicit selection via --select
                enabled_overrides[op.operation_key] = op.operation_key in selected_set or (
                    op.operation_id in selected_set if op.operation_id else False
                )
            elif read_only:
                enabled_overrides[op.operation_key] = (
                    is_read_only_method(op.method) and not op.deprecated
                )
            else:
                def_enabled, _, _ = determine_default_selection(op)
                enabled_overrides[op.operation_key] = def_enabled

        # Map to toolset
        toolset = map_api_to_toolset(
            ir=ir,
            tool_prefix=tool_prefix,
            enabled_overrides=enabled_overrides,
            generator_version=__version__,
        )

        # Review spec
        report = review_api(
            ir=ir,
            toolset=toolset,
            raw_text=raw_text,
            raw_spec_dict=parsed.raw_dict,
        )
        if report.has_blocking_errors:
            unacked = [f.message for f in report.findings if f.severity == "error"]
            if json_output:
                typer.echo(
                    json.dumps(
                        {"error": "Specification has blocking review errors", "details": unacked}
                    )
                )
            else:
                typer.secho(
                    f"✗ Generation blocked by errors: {'; '.join(unacked)}",
                    fg=typer.colors.RED,
                    err=True,
                )
            raise typer.Exit(code=1) from None

        manifest = toolset.to_manifest()
        if base_url:
            manifest.info.base_url = base_url

        # Derive slug from title or output dir name
        slug = re.sub(r"[^a-zA-Z0-9_-]", "-", ir.title.lower()).strip("-")[:64] or "server"

        # Render project
        output.mkdir(parents=True, exist_ok=True)
        render_project(manifest, output, slug=slug)

        res_data = {
            "status": "success",
            "output_dir": str(output.resolve()),
            "tool_count": manifest.tool_count,
            "warning_count": report.warning_count,
        }

        if json_output:
            typer.echo(json.dumps(res_data, indent=2))
        else:
            typer.secho(f"[OK] Generated MCP server in: {output.resolve()}", fg=typer.colors.GREEN)
            typer.echo(f"  Tools enabled: {manifest.tool_count}")
            typer.echo(f"  Warnings: {report.warning_count}")
        return

    except typer.Exit:
        raise
    except ForgeError as fe:
        if json_output:
            typer.echo(json.dumps({"error": fe.to_dict()["error"]}))
        else:
            typer.secho(f"Generation error: {fe.message}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from None


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", help="Host interface to bind"),
    port: int = typer.Option(8080, "--port", help="Port to listen on"),
) -> None:
    """Start the MCP Forge FastAPI server."""
    import uvicorn

    settings = Settings(forge_host=host, forge_port=port)
    app_instance = create_app(settings)
    uvicorn.run(app_instance, host=host, port=port)


@app.command()
def samples(
    json_output: bool = typer.Option(False, "--json", help="Output samples as JSON"),
    seed: bool = typer.Option(
        False, "--seed", help="Seed all bundled sample specifications into local database"
    ),
) -> None:
    """List or seed bundled sample specifications."""
    known_samples = [
        {
            "id": "bookshop",
            "file": "bookshop.openapi.yaml",
            "desc": "Bookshop API (OpenAPI 3.0)",
            "title": "Bookshop API",
            "format": "yaml",
        },
        {
            "id": "tasks",
            "file": "tasks.openapi.json",
            "desc": "Task Management API (OpenAPI 3.0)",
            "title": "Task Management API",
            "format": "json",
        },
        {
            "id": "legacy",
            "file": "legacy-swagger2.json",
            "desc": "Legacy Swagger API (Swagger 2.0)",
            "title": "Legacy Swagger API",
            "format": "json",
        },
    ]

    if seed:

        async def _seed_samples() -> list[str]:
            import hashlib

            from sqlalchemy import select

            from mcp_forge.db.models.project import Project
            from mcp_forge.db.models.project_settings import ProjectSettings
            from mcp_forge.db.models.spec_version import SpecVersion
            from mcp_forge.db.session import get_db_session

            seeded_names: list[str] = []
            async with get_db_session() as db:
                for s in known_samples:
                    f = SAMPLES_DIR / s["file"]
                    if not f.exists():
                        continue

                    slug = f"{s['id']}-sample"
                    stmt = select(Project).where(Project.slug == slug)
                    existing = (await db.execute(stmt)).scalar_one_or_none()
                    if existing:
                        continue

                    raw_text = f.read_text(encoding="utf-8")
                    parsed = parse_and_validate(raw_text)
                    ir = normalize_spec(parsed)

                    project = Project(name=s["title"], slug=slug)
                    db.add(project)
                    await db.flush()

                    base_url = ir.servers[0].url if ir.servers else "http://127.0.0.1:8000"
                    db.add(ProjectSettings(project_id=project.id, base_url=base_url))

                    sha256 = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
                    db.add(
                        SpecVersion(
                            project_id=project.id,
                            version_no=1,
                            source_type="sample",
                            source_ref=s["file"],
                            format=s["format"],
                            spec_kind=parsed.kind,
                            sha256=sha256,
                            raw_text=raw_text,
                            operation_count=len(ir.operations),
                        )
                    )
                    await db.commit()
                    seeded_names.append(s["title"])
            return seeded_names

        created = asyncio.run(_seed_samples())
        if json_output:
            typer.echo(json.dumps({"seeded": created, "count": len(created)}))
        else:
            if created:
                typer.secho(
                    f"[OK] Successfully seeded {len(created)} sample project(s):",
                    fg=typer.colors.GREEN,
                )
                for name in created:
                    typer.echo(f"  + {name}")
            else:
                typer.echo("All bundled sample projects are already seeded in the database.")
        return

    results = []
    for s in known_samples:
        f = SAMPLES_DIR / s["file"]
        results.append(
            {
                "id": s["id"],
                "file": s["file"],
                "description": s["desc"],
                "exists": f.exists(),
            }
        )

    if json_output:
        typer.echo(json.dumps(results, indent=2))
    else:
        typer.secho("Bundled OpenAPI/Swagger Samples:", fg=typer.colors.CYAN)
        for r in results:
            typer.echo(f"  * {r['id']}: {r['description']} ({r['file']})")


@app.command()
def wipe(
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm deletion without prompting"),
) -> None:
    """Wipe all stored local data and SQLite database."""
    if not yes:
        confirm = typer.confirm(
            "Are you sure you want to delete all stored MCP Forge projects and data?"
        )
        if not confirm:
            typer.echo("Wipe aborted.")
            raise typer.Exit(code=0)

    settings = Settings()
    data_dir = settings.forge_data_dir
    if data_dir.exists():
        shutil.rmtree(data_dir, ignore_errors=True)
        typer.secho(f"[OK] Wiped all data in {data_dir}", fg=typer.colors.GREEN)
    else:
        typer.echo("Data directory is already empty.")


if __name__ == "__main__":
    app()
