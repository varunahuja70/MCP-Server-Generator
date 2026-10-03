"""Data models for review lint findings and reports."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SeverityLevel = Literal["error", "warning", "info"]


class ReviewFinding(BaseModel):
    """An individual lint or security finding produced during review."""

    model_config = ConfigDict(extra="ignore")

    code: str
    severity: SeverityLevel
    message: str
    operation_key: str | None = None
    suggestion: str | None = None
    acknowledged: bool = False


class ReviewReport(BaseModel):
    """Aggregated review findings and blocking status."""

    model_config = ConfigDict(extra="ignore")

    findings: list[ReviewFinding] = Field(default_factory=list)

    @property
    def has_blocking_errors(self) -> bool:
        """Returns True if there are any unacknowledged error findings."""
        return any(f.severity == "error" and not f.acknowledged for f in self.findings)

    @property
    def error_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "warning")

    @property
    def info_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "info")
