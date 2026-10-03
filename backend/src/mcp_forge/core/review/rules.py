"""Implementation of all review lint and security rules."""

import difflib
from typing import Any
from urllib.parse import urlparse

from mcp_forge.core.ir.models import IRApi
from mcp_forge.core.mapping.manifest import ToolSet
from mcp_forge.core.review.models import ReviewFinding
from mcp_forge.core.review.patterns import INSTRUCTION_PATTERNS, KEY_LIKE_PATTERNS
from mcp_forge.core.security.ssrf import validate_url_ssrf
from mcp_forge.core.security.unicode import clean_unicode_text
from mcp_forge.errors import SSRFBlockedError


def check_spec_002(toolset: ToolSet) -> list[ReviewFinding]:
    """SPEC-002: Feature not supported, operation skipped."""
    findings: list[ReviewFinding] = []
    for tool in toolset.mapped_tools:
        if tool.skipped and tool.skipped_reason:
            findings.append(
                ReviewFinding(
                    code="SPEC-002",
                    severity="warning",
                    message=f"Operation '{tool.manifest_tool.name}' was skipped: {tool.skipped_reason}",
                    operation_key=tool.manifest_tool.operation_key,
                    suggestion="Review operation requirements or configure manual overrides.",
                )
            )
    return findings


def check_sec_001(raw_spec_dict: dict[str, Any]) -> list[ReviewFinding]:
    """SEC-001: Invisible or bidirectional control characters found in names or descriptions."""
    findings: list[ReviewFinding] = []

    def _walk(obj: Any, path: str = "") -> None:
        if isinstance(obj, str):
            _, has_stripped, count = clean_unicode_text(obj)
            if has_stripped:
                findings.append(
                    ReviewFinding(
                        code="SEC-001",
                        severity="error",
                        message=f"Found {count} invisible, bidi, or control characters in '{path}'. They have been stripped for safety.",
                        suggestion="Acknowledge this finding to proceed with generation.",
                    )
                )
        elif isinstance(obj, dict):
            for k, v in obj.items():
                _walk(k, f"{path}/{k}#key")
                _walk(v, f"{path}/{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                _walk(item, f"{path}[{i}]")

    _walk(raw_spec_dict, "root")
    return findings


def check_sec_002(toolset: ToolSet) -> list[ReviewFinding]:
    """SEC-002: Description contains instruction-like text aimed at an AI agent."""
    findings: list[ReviewFinding] = []
    for tool in toolset.mapped_tools:
        desc = tool.manifest_tool.description
        summary = tool.manifest_tool.summary or ""
        text_to_scan = f"{summary} {desc}"

        for name, pattern in INSTRUCTION_PATTERNS:
            match = pattern.search(text_to_scan)
            if match:
                snippet = match.group(0)
                findings.append(
                    ReviewFinding(
                        code="SEC-002",
                        severity="warning",
                        message=f"Tool '{tool.manifest_tool.name}' description contains suspicious pattern '{name}' ('{snippet}').",
                        operation_key=tool.manifest_tool.operation_key,
                        suggestion="Edit the description to remove instructions, external URLs, or prompt injection phrasing.",
                    )
                )
                break
    return findings


def check_sec_003(toolset: ToolSet) -> list[ReviewFinding]:
    """SEC-003: Write or delete tool enabled."""
    findings: list[ReviewFinding] = []
    for tool in toolset.mapped_tools:
        if tool.enabled:
            m = tool.manifest_tool.method.upper()
            if m in ("POST", "PUT", "PATCH", "DELETE"):
                findings.append(
                    ReviewFinding(
                        code="SEC-003",
                        severity="warning",
                        message=f"Write/modify tool '{tool.manifest_tool.name}' ({m} {tool.manifest_tool.path}) is enabled.",
                        operation_key=tool.manifest_tool.operation_key,
                        suggestion="Ensure this modifying operation is intended and verify access controls.",
                    )
                )
    return findings


def check_sec_004(ir: IRApi) -> list[ReviewFinding]:
    """SEC-004: Server URL points to a private or local address."""
    findings: list[ReviewFinding] = []
    for server in ir.servers:
        url = server.url
        if not url:
            continue
        parsed = urlparse(url)
        if parsed.scheme.lower() in ("http", "https"):
            try:
                validate_url_ssrf(url, allow_private=False)
            except SSRFBlockedError as e:
                findings.append(
                    ReviewFinding(
                        code="SEC-004",
                        severity="warning",
                        message=f"Server URL '{url}' points to a local or private address: {e.message}",
                        suggestion="The generated server requires ALLOW_PRIVATE_TARGETS=true in its environment to call this URL.",
                    )
                )
    return findings


def check_sec_005(ir: IRApi, has_sec_004: bool) -> list[ReviewFinding]:
    """SEC-005: No authentication scheme found for an API that looks private."""
    findings: list[ReviewFinding] = []
    if has_sec_004 and not ir.security_schemes:
        findings.append(
            ReviewFinding(
                code="SEC-005",
                severity="info",
                message="Target server points to a private/local network, but no authentication schemes are defined.",
                suggestion="Add API keys, HTTP bearer, or basic auth if this private service requires authentication.",
            )
        )
    return findings


def check_sec_006(raw_text: str) -> list[ReviewFinding]:
    """SEC-006: Spec contains strings that look like live keys or credentials."""
    findings: list[ReviewFinding] = []
    for name, pattern in KEY_LIKE_PATTERNS:
        match = pattern.search(raw_text)
        if match:
            findings.append(
                ReviewFinding(
                    code="SEC-006",
                    severity="warning",
                    message=f"Specification appears to contain a live credential or secret matching pattern '{name}'.",
                    suggestion="Remove real API keys, tokens, or private keys from your OpenAPI spec and use environment variables.",
                )
            )
    return findings


def check_qual_001(toolset: ToolSet) -> list[ReviewFinding]:
    """QUAL-001: Missing or very short description."""
    findings: list[ReviewFinding] = []
    for tool in toolset.mapped_tools:
        if not tool.skipped:
            desc = tool.manifest_tool.description.strip()
            if not desc or len(desc) < 10 or desc == "No description provided.":
                findings.append(
                    ReviewFinding(
                        code="QUAL-001",
                        severity="warning",
                        message=f"Tool '{tool.manifest_tool.name}' has no description or an extremely short description.",
                        operation_key=tool.manifest_tool.operation_key,
                        suggestion="Provide a clear description so LLM agents know when and how to call this tool.",
                    )
                )
    return findings


def check_qual_002(toolset: ToolSet, max_tools: int = 40) -> list[ReviewFinding]:
    """QUAL-002: More than 40 tools enabled."""
    findings: list[ReviewFinding] = []
    enabled = toolset.enabled_count
    if enabled > max_tools:
        findings.append(
            ReviewFinding(
                code="QUAL-002",
                severity="warning",
                message=f"{enabled} tools are enabled (recommended maximum is {max_tools}). Large toolsets may degrade LLM reasoning and exceed context budgets.",
                suggestion="Disable infrequently used tools or select a narrower preset.",
            )
        )
    return findings


def check_qual_003(toolset: ToolSet) -> list[ReviewFinding]:
    """QUAL-003: Name collision resolved."""
    findings: list[ReviewFinding] = []
    for tool in toolset.mapped_tools:
        if tool.had_collision:
            findings.append(
                ReviewFinding(
                    code="QUAL-003",
                    severity="info",
                    message=f"Tool name collision resolved by assigning unique name '{tool.manifest_tool.name}'.",
                    operation_key=tool.manifest_tool.operation_key,
                    suggestion="You can customize this name using an operation override in settings.",
                )
            )
    return findings


def check_qual_004(toolset: ToolSet) -> list[ReviewFinding]:
    """QUAL-004: Input schema very large or cut at depth limit."""
    findings: list[ReviewFinding] = []
    for tool in toolset.mapped_tools:
        schema = tool.manifest_tool.input_schema
        schema_str = str(schema)
        if (
            "x-cut-depth" in schema_str
            or "x-truncated" in schema_str
            or "x-circular-ref" in schema_str
        ):
            findings.append(
                ReviewFinding(
                    code="QUAL-004",
                    severity="warning",
                    message=f"Tool '{tool.manifest_tool.name}' has an input schema that was simplified due to depth limit, size, or circular reference.",
                    operation_key=tool.manifest_tool.operation_key,
                    suggestion="Verify that the simplified arguments allow all necessary parameters to be passed.",
                )
            )
    return findings


def check_qual_005(toolset: ToolSet) -> list[ReviewFinding]:
    """QUAL-005: Operation deprecated."""
    findings: list[ReviewFinding] = []
    for tool in toolset.mapped_tools:
        if tool.deprecated:
            findings.append(
                ReviewFinding(
                    code="QUAL-005",
                    severity="info",
                    message=f"Operation '{tool.manifest_tool.name}' is marked deprecated in the specification.",
                    operation_key=tool.manifest_tool.operation_key,
                    suggestion="Consider using modern non-deprecated endpoints if available.",
                )
            )
    return findings


def check_qual_006(toolset: ToolSet) -> list[ReviewFinding]:
    """QUAL-006: Ambiguous names or near-duplicate descriptions across tools."""
    findings: list[ReviewFinding] = []
    tools = [t for t in toolset.mapped_tools if t.enabled and not t.skipped]

    for i in range(len(tools)):
        for j in range(i + 1, len(tools)):
            t1 = tools[i]
            t2 = tools[j]
            d1 = t1.manifest_tool.description.lower()
            d2 = t2.manifest_tool.description.lower()
            if len(d1) > 20 and len(d2) > 20:
                matcher = difflib.SequenceMatcher(None, d1, d2)
                if matcher.ratio() > 0.90:
                    findings.append(
                        ReviewFinding(
                            code="QUAL-006",
                            severity="warning",
                            message=f"Tools '{t1.manifest_tool.name}' and '{t2.manifest_tool.name}' have nearly identical descriptions (similarity > 90%).",
                            operation_key=t1.manifest_tool.operation_key,
                            suggestion="Refine tool descriptions to help agents differentiate between them.",
                        )
                    )
    return findings
