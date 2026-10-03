"""Review engine that executes all security and quality lint checks against the specification."""

from typing import Any

from mcp_forge.core.ir.models import IRApi
from mcp_forge.core.mapping.manifest import ToolSet
from mcp_forge.core.review.models import ReviewFinding, ReviewReport
from mcp_forge.core.review.rules import (
    check_qual_001,
    check_qual_002,
    check_qual_003,
    check_qual_004,
    check_qual_005,
    check_qual_006,
    check_sec_001,
    check_sec_002,
    check_sec_003,
    check_sec_004,
    check_sec_005,
    check_sec_006,
    check_spec_002,
)


def review_api(
    ir: IRApi,
    toolset: ToolSet,
    raw_text: str = "",
    raw_spec_dict: dict[str, Any] | None = None,
    acknowledged_findings: set[tuple[str, str | None]] | None = None,
    max_tools_threshold: int = 40,
) -> ReviewReport:
    """Run all review checks and produce a unified ReviewReport.

    acknowledged_findings is a set of (code, operation_key) tuples representing findings
    that the user has explicitly acknowledged.
    """
    findings: list[ReviewFinding] = []
    ack_set = acknowledged_findings or set()

    # SPEC rules
    findings.extend(check_spec_002(toolset))

    # SEC rules
    if raw_spec_dict:
        findings.extend(check_sec_001(raw_spec_dict))

    findings.extend(check_sec_002(toolset))
    findings.extend(check_sec_003(toolset))

    sec_004_findings = check_sec_004(ir)
    findings.extend(sec_004_findings)
    findings.extend(check_sec_005(ir, has_sec_004=len(sec_004_findings) > 0))

    if raw_text:
        findings.extend(check_sec_006(raw_text))

    # QUAL rules
    findings.extend(check_qual_001(toolset))
    findings.extend(check_qual_002(toolset, max_tools=max_tools_threshold))
    findings.extend(check_qual_003(toolset))
    findings.extend(check_qual_004(toolset))
    findings.extend(check_qual_005(toolset))
    findings.extend(check_qual_006(toolset))

    # Apply acknowledgement status
    for f in findings:
        key = (f.code, f.operation_key)
        if key in ack_set or (f.code, None) in ack_set:
            f.acknowledged = True

    return ReviewReport(findings=findings)
