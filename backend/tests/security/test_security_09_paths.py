"""Security Test 9: Path traversal defense and containment."""

from pathlib import Path

import pytest

from mcp_forge.core.security.paths import safe_join
from mcp_forge.errors import ForgeError


def test_safe_relative_path_resolves_inside_base(tmp_path: Path) -> None:
    base = tmp_path / "artifacts"
    base.mkdir()

    resolved = safe_join(base, "server/runtime/config.py")
    assert resolved == (base / "server" / "runtime" / "config.py").resolve()
    assert resolved.is_relative_to(base.resolve())


def test_path_traversal_attempts_rejected(tmp_path: Path) -> None:
    base = tmp_path / "artifacts"
    base.mkdir()

    hostile_paths = [
        "../secret.txt",
        "../../etc/passwd",
        "..\\..\\Windows\\System32",
        "nested/../../secret.txt",
        "/etc/passwd",
        "//server/share",
        "C:\\Windows\\System32",
        "D:/Data/secrets",
        "safe_file.txt\0.evil.py",
    ]
    for path in hostile_paths:
        with pytest.raises(ForgeError) as exc_info:
            safe_join(base, path)
        assert exc_info.value.code == "PATH_TRAVERSAL_DETECTED"


def test_build_file_browser_traversal_attempts_rejected(tmp_path: Path) -> None:
    """get_build_file_content safely rejects path traversal attempts."""
    from mcp_forge.services.builds import get_build_file_content

    base = tmp_path / "project"
    base.mkdir()
    (base / "server.py").write_text("ok", encoding="utf-8")

    hostile_paths = [
        "../secret.txt",
        "../../etc/passwd",
        "/etc/passwd",
        "nested/../../secret.txt",
        "C:\\Windows\\System32",
    ]
    for path in hostile_paths:
        with pytest.raises(ForgeError) as exc_info:
            get_build_file_content(base, path)
        assert exc_info.value.code == "PATH_TRAVERSAL_DETECTED"
