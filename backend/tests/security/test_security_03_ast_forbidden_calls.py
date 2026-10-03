"""Security test 03: AST scanner detects and rejects forbidden calls in generated python."""

from pathlib import Path

import pytest

from mcp_forge.core.render.check_output import scan_file_ast
from mcp_forge.errors import SecurityError, ValidationError


def test_ast_scanner_detects_forbidden_builtins(tmp_path: Path) -> None:
    """ast scanner rejects eval, exec, compile, __import__."""
    forbidden_snippets = [
        "eval('1 + 1')",
        "exec('import sys')",
        "compile('x = 1', '<string>', 'exec')",
        "__import__('os')",
    ]

    for snippet in forbidden_snippets:
        file = tmp_path / f"test_{abs(hash(snippet))}.py"
        file.write_text(f"def bad():\n    {snippet}\n", encoding="utf-8")
        with pytest.raises(SecurityError, match="Forbidden function call"):
            scan_file_ast(file)


def test_ast_scanner_detects_forbidden_os_calls(tmp_path: Path) -> None:
    """ast scanner rejects os.system, os.popen, os.spawn*."""
    forbidden_snippets = [
        "os.system('id')",
        "os.popen('whoami')",
        "os.spawnl(os.P_WAIT, '/bin/ls', 'ls')",
    ]

    for snippet in forbidden_snippets:
        file = tmp_path / f"test_{abs(hash(snippet))}.py"
        file.write_text(f"import os\ndef bad():\n    {snippet}\n", encoding="utf-8")
        with pytest.raises(SecurityError, match="Forbidden OS execution call"):
            scan_file_ast(file)


def test_ast_scanner_detects_forbidden_subprocess_calls(tmp_path: Path) -> None:
    """ast scanner rejects subprocess calls."""
    forbidden_snippets = [
        "subprocess.run(['ls'])",
        "subprocess.Popen(['bash'])",
        "subprocess.call(['id'])",
        "subprocess.check_call(['pwd'])",
        "subprocess.check_output(['uname'])",
    ]

    for snippet in forbidden_snippets:
        file = tmp_path / f"test_{abs(hash(snippet))}.py"
        file.write_text(f"import subprocess\ndef bad():\n    {snippet}\n", encoding="utf-8")
        with pytest.raises(SecurityError, match="Forbidden process spawn"):
            scan_file_ast(file)


def test_ast_scanner_allows_benign_python_code(tmp_path: Path) -> None:
    """ast scanner accepts safe valid python code."""
    safe_code = """
import sys
import json
from pathlib import Path

def greet(name: str) -> str:
    return f"Hello, {name}"

data = json.loads('{"key": "val"}')
"""
    file = tmp_path / "safe.py"
    file.write_text(safe_code, encoding="utf-8")
    # Should not raise
    scan_file_ast(file)


def test_ast_scanner_raises_validation_error_on_syntax_error(tmp_path: Path) -> None:
    """ast scanner raises ValidationError on invalid syntax."""
    file = tmp_path / "broken.py"
    file.write_text("def broken_func(:\n    pass", encoding="utf-8")
    with pytest.raises(ValidationError, match="Syntax error in generated file"):
        scan_file_ast(file)
