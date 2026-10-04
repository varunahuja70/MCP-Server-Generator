"""Diff engine for comparing two spec versions or operation sets."""

from pydantic import BaseModel, Field

from mcp_forge.core.ir import normalize_spec
from mcp_forge.core.ir.models import IRApi
from mcp_forge.core.parse import parse_and_validate


class OperationDiff(BaseModel):
    """Diff summary of an operation between two specifications."""

    operation_key: str
    method: str
    path: str
    diff_type: str  # "added" | "removed" | "modified" | "unchanged"
    changes: list[str] = Field(default_factory=list)


class SpecDiffReport(BaseModel):
    """Complete diff report between two spec versions."""

    base_version_no: int | None
    target_version_no: int | None
    added_count: int = 0
    removed_count: int = 0
    modified_count: int = 0
    unchanged_count: int = 0
    operations: list[OperationDiff] = Field(default_factory=list)
    title_changed: bool = False
    version_changed: bool = False
    servers_changed: bool = False


def diff_ir_apis(
    base_ir: IRApi,
    target_ir: IRApi,
    base_version_no: int | None = None,
    target_version_no: int | None = None,
) -> SpecDiffReport:
    """Compare two normalized IRApi models and produce a detailed diff report."""
    base_ops = {op.operation_key: op for op in base_ir.operations}
    target_ops = {op.operation_key: op for op in target_ir.operations}

    all_keys = sorted(set(base_ops.keys()) | set(target_ops.keys()))

    diffs: list[OperationDiff] = []
    added = 0
    removed = 0
    modified = 0
    unchanged = 0

    for key in all_keys:
        in_base = key in base_ops
        in_target = key in target_ops

        if in_target and not in_base:
            top = target_ops[key]
            diffs.append(
                OperationDiff(
                    operation_key=key,
                    method=top.method,
                    path=top.path,
                    diff_type="added",
                    changes=["Operation added"],
                )
            )
            added += 1
        elif in_base and not in_target:
            bop = base_ops[key]
            diffs.append(
                OperationDiff(
                    operation_key=key,
                    method=bop.method,
                    path=bop.path,
                    diff_type="removed",
                    changes=["Operation removed"],
                )
            )
            removed += 1
        else:
            bop = base_ops[key]
            top = target_ops[key]
            changes: list[str] = []

            if bop.summary != top.summary:
                changes.append(f"Summary changed from '{bop.summary}' to '{top.summary}'")
            if bop.description != top.description:
                changes.append("Description modified")
            if bop.deprecated != top.deprecated:
                changes.append(f"Deprecated changed to {top.deprecated}")

            # Parameters check
            b_params = {p.name: p for p in bop.parameters}
            t_params = {p.name: p for p in top.parameters}
            added_p = set(t_params.keys()) - set(b_params.keys())
            removed_p = set(b_params.keys()) - set(t_params.keys())
            if added_p:
                changes.append(f"Parameters added: {', '.join(sorted(added_p))}")
            if removed_p:
                changes.append(f"Parameters removed: {', '.join(sorted(removed_p))}")

            # Request body check
            if bool(bop.request_body) != bool(top.request_body):
                changes.append("Request body added or removed")

            # Responses check
            b_resps = set(bop.responses.keys())
            t_resps = set(top.responses.keys())
            if b_resps != t_resps:
                changes.append(f"Responses changed ({len(b_resps)} -> {len(t_resps)})")

            if changes:
                diffs.append(
                    OperationDiff(
                        operation_key=key,
                        method=top.method,
                        path=top.path,
                        diff_type="modified",
                        changes=changes,
                    )
                )
                modified += 1
            else:
                diffs.append(
                    OperationDiff(
                        operation_key=key,
                        method=top.method,
                        path=top.path,
                        diff_type="unchanged",
                        changes=[],
                    )
                )
                unchanged += 1

    return SpecDiffReport(
        base_version_no=base_version_no,
        target_version_no=target_version_no,
        added_count=added,
        removed_count=removed,
        modified_count=modified,
        unchanged_count=unchanged,
        operations=diffs,
        title_changed=base_ir.title != target_ir.title,
        version_changed=base_ir.version != target_ir.version,
        servers_changed=[s.url for s in base_ir.servers] != [s.url for s in target_ir.servers],
    )


def diff_spec_texts(
    base_text: str,
    target_text: str,
    base_version_no: int | None = None,
    target_version_no: int | None = None,
) -> SpecDiffReport:
    """Parse, normalize and diff two raw specification texts."""
    base_parsed = parse_and_validate(base_text)
    target_parsed = parse_and_validate(target_text)

    base_ir = normalize_spec(base_parsed)
    target_ir = normalize_spec(target_parsed)

    return diff_ir_apis(
        base_ir,
        target_ir,
        base_version_no=base_version_no,
        target_version_no=target_version_no,
    )
