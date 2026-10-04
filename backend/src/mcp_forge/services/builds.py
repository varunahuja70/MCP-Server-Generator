"""Build pipeline, file exploration, connection snippets, and artifact management service."""

import asyncio
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mcp_forge.config import get_settings
from mcp_forge.core.ir import normalize_spec
from mcp_forge.core.mapping.manifest import ManifestDoc
from mcp_forge.core.mapping.mapper import map_api_to_toolset
from mcp_forge.core.parse import parse_and_validate
from mcp_forge.core.render.package import create_deterministic_zip
from mcp_forge.core.render.renderer import render_project
from mcp_forge.core.security.paths import safe_join
from mcp_forge.db.models.build import Build
from mcp_forge.db.models.operation_config import OperationConfig
from mcp_forge.db.models.project import Project
from mcp_forge.db.models.project_settings import ProjectSettings
from mcp_forge.db.models.spec_version import SpecVersion
from mcp_forge.db.uuid_helper import utcnow_iso
from mcp_forge.errors import ForgeError, NotFoundError, SecurityError, ValidationError
from mcp_forge.services.review import run_spec_review
from mcp_forge.version import __version__


class BuildPipelineResult(BaseModel):
    """Result of running the build pipeline."""

    build_id: str
    build_no: int
    status: str
    tool_count: int
    warning_count: int
    artifact_path: str
    artifact_sha256: str
    error_message_safe: str | None = None


def get_build_dir(data_dir: Path, slug: str, build_no: int) -> Path:
    """Return canonical directory for a build's artifacts."""
    return data_dir / "builds" / slug / f"build_{build_no}"


def get_server_dir(data_dir: Path, slug: str, build_no: int) -> Path:
    """Return canonical directory for the generated server project code."""
    return get_build_dir(data_dir, slug, build_no) / f"{slug}-mcp"


def get_zip_path(data_dir: Path, slug: str, build_no: int) -> Path:
    """Return canonical archive zip path for a build."""
    return get_build_dir(data_dir, slug, build_no) / f"{slug}-mcp.zip"


def resolve_build_paths(build: Build, slug: str) -> tuple[Path, Path]:
    """Canonically resolve (server_dir, zip_path) for an existing build."""
    if build.artifact_path:
        zip_path = Path(build.artifact_path)
        server_dir = zip_path.parent / f"{slug}-mcp"
        if not server_dir.exists():
            candidate = zip_path.with_suffix("")
            if candidate.exists():
                server_dir = candidate
            elif (zip_path.parent / "server").exists():
                server_dir = zip_path.parent / "server"
        return server_dir, zip_path

    settings = get_settings()
    server_dir = get_server_dir(settings.forge_data_dir, slug, build.build_no)
    zip_path = get_zip_path(settings.forge_data_dir, slug, build.build_no)
    return server_dir, zip_path


def generate_client_snippets(
    project_slug: str,
    server_dir: Path | str,
    required_env_vars: list[str] | None = None,
) -> dict[str, Any]:
    """Generate ready-to-use client connection snippets for major MCP client apps."""
    abs_server_dir = Path(server_dir).resolve().as_posix()
    required_env_vars = required_env_vars or []
    env_dict = {var: f"${{{var}}}" for var in required_env_vars}

    # 1. Claude Desktop config snippet (claude_desktop_config.json)
    claude_desktop = {
        "mcpServers": {
            f"{project_slug}-mcp": {
                "command": "python",
                "args": ["-m", "server"],
                "cwd": abs_server_dir,
                "env": env_dict,
            }
        }
    }

    # 2. Cursor IDE snippet (.cursor/mcp.json)
    cursor_config = {
        "mcpServers": {
            f"{project_slug}-mcp": {
                "command": "python",
                "args": [f"{abs_server_dir}/server.py"],
                "env": env_dict,
            }
        }
    }

    # 3. CLI stdio run command
    cli_command = f"python {abs_server_dir}/server.py"

    # 4. Streamable HTTP run command
    http_command = f"python {abs_server_dir}/server.py --http --host 127.0.0.1 --port 8000"

    return {
        "claude_desktop": json.dumps(claude_desktop, indent=2),
        "cursor": json.dumps(cursor_config, indent=2),
        "cli_stdio": cli_command,
        "cli_http": http_command,
        "required_env_vars": required_env_vars,
    }


def list_build_file_tree(project_dir: Path, root_dir: Path | None = None) -> list[dict[str, Any]]:
    """List project directory tree recursively in a sorted hierarchical structure."""
    if not project_dir.exists():
        return []

    base = root_dir if root_dir is not None else project_dir
    items: list[dict[str, Any]] = []
    for entry in sorted(project_dir.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        rel = entry.relative_to(base).as_posix()
        if entry.is_dir():
            items.append(
                {
                    "name": entry.name,
                    "path": rel,
                    "type": "directory",
                    "children": list_build_file_tree(entry, root_dir=base),
                }
            )
        else:
            items.append(
                {
                    "name": entry.name,
                    "path": rel,
                    "type": "file",
                    "size": entry.stat().st_size,
                }
            )
    return items


def get_build_file_content(project_dir: Path, relative_path: str) -> str:
    """Read file content safely within project_dir using path containment check."""
    target_path = safe_join(project_dir, relative_path)
    if not target_path.exists():
        raise NotFoundError(f"File '{relative_path}' not found in build directory.")
    if not target_path.is_file():
        raise ValidationError(f"Target path '{relative_path}' is a directory, not a file.")

    return target_path.read_text(encoding="utf-8")


async def create_build_for_project(
    session: AsyncSession,
    project_id: str,
    spec_version_id: str | None = None,
    timeout_s: float | None = None,
) -> Build:
    """Execute complete build pipeline: review -> map -> render -> ast check -> package zip -> store."""
    settings = get_settings()
    pipeline_timeout = timeout_s or settings.pipeline_timeout_s

    # 1. Fetch project
    project = await session.get(Project, project_id)
    if not project:
        raise NotFoundError(f"Project with ID '{project_id}' not found.")

    # 2. Determine spec version
    if not spec_version_id:
        stmt_spec = (
            select(SpecVersion)
            .where(SpecVersion.project_id == project_id)
            .order_by(SpecVersion.version_no.desc())
        )
        res_spec = await session.execute(stmt_spec)
        spec_version = res_spec.scalars().first()
        if not spec_version:
            raise ValidationError(f"Project '{project.name}' has no imported spec versions.")
    else:
        spec_version = await session.get(SpecVersion, spec_version_id)
        if not spec_version:
            raise NotFoundError(f"SpecVersion with ID '{spec_version_id}' not found.")

    # 3. Determine next build_no
    stmt_no = select(func.coalesce(func.max(Build.build_no), 0)).where(
        Build.project_id == project_id
    )
    res_no = await session.execute(stmt_no)
    next_build_no = res_no.scalar_one() + 1

    dist_dir = get_server_dir(settings.forge_data_dir, project.slug, next_build_no)
    zip_path = get_zip_path(settings.forge_data_dir, project.slug, next_build_no)

    # Create Build record in database
    build = Build(
        project_id=project_id,
        spec_version_id=spec_version.id,
        build_no=next_build_no,
        status="running",
        generator_version=__version__,
        artifact_path=str(zip_path),
        artifact_sha256="",
        tool_count=0,
        warning_count=0,
    )
    session.add(build)
    await session.commit()
    await session.refresh(build)

    async def _execute_pipeline() -> tuple[ManifestDoc, str, int, int]:
        # Review spec
        review_report = await run_spec_review(
            session=session,
            project_id=project_id,
            spec_version_id=spec_version.id,
            build_id=build.id,
        )

        # Blocking findings check
        if review_report.has_blocking_errors:
            unacked = [
                f.message
                for f in review_report.findings
                if f.severity == "error" and not f.acknowledged
            ]
            raise SecurityError(
                f"Build blocked by {len(unacked)} unacknowledged security/specification error(s): {'; '.join(unacked)}",
                details={"errors": unacked},
            )

        # Normalization and tool mapping
        parsed = parse_and_validate(spec_version.raw_text)
        ir = normalize_spec(parsed)

        # Get project settings and overrides
        proj_settings = await session.get(ProjectSettings, project_id)
        tool_prefix = proj_settings.tool_prefix if proj_settings else None

        stmt_ops = select(OperationConfig).where(OperationConfig.project_id == project_id)
        res_ops = await session.execute(stmt_ops)
        op_configs = res_ops.scalars().all()

        name_overrides = {
            op.operation_key: op.tool_name_override for op in op_configs if op.tool_name_override
        }
        desc_overrides = {
            op.operation_key: op.description_override
            for op in op_configs
            if op.description_override
        }
        enabled_overrides = {op.operation_key: op.enabled for op in op_configs}

        toolset = map_api_to_toolset(
            ir=ir,
            tool_prefix=tool_prefix,
            name_overrides=name_overrides,
            description_overrides=desc_overrides,
            enabled_overrides=enabled_overrides,
            generator_version=__version__,
        )

        manifest = toolset.to_manifest()
        if proj_settings and proj_settings.base_url:
            manifest.info.base_url = proj_settings.base_url

        # Render project directory
        render_project(manifest, dist_dir, slug=project.slug)

        # Create deterministic zip
        _, sha256_hex = create_deterministic_zip(dist_dir, zip_path)

        return manifest, sha256_hex, manifest.tool_count, review_report.warning_count

    try:
        manifest, sha256_hex, tool_count, warning_count = await asyncio.wait_for(
            _execute_pipeline(),
            timeout=pipeline_timeout,
        )
        build.status = "succeeded"
        build.artifact_sha256 = sha256_hex
        build.tool_count = tool_count
        build.warning_count = warning_count
        build.finished_at = utcnow_iso()
    except TimeoutError:
        build.status = "failed"
        build.error_message_safe = f"Build pipeline timed out after {pipeline_timeout}s."
        build.finished_at = utcnow_iso()
    except ForgeError as e:
        build.status = "failed"
        build.error_message_safe = e.message
        build.finished_at = utcnow_iso()
    except Exception as e:
        build.status = "failed"
        build.error_message_safe = f"Internal build error: {str(e)}"
        build.finished_at = utcnow_iso()

    await session.commit()
    await session.refresh(build)
    return build
