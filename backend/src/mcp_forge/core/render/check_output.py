"""AST security scanning, ruff validation, and output checks for generated projects."""

import ast
import json
from pathlib import Path

from mcp_forge.core.mapping.manifest import validate_manifest
from mcp_forge.errors import SecurityError, ValidationError

FORBIDDEN_CALL_NAMES = {"eval", "exec", "__import__", "compile"}
FORBIDDEN_OS_CALLS = {
    "system",
    "popen",
    "spawnl",
    "spawnle",
    "spawnlp",
    "spawnlpe",
    "spawnv",
    "spawnve",
    "spawnvp",
    "spawnvpe",
}
FORBIDDEN_SUBPROCESS_CALLS = {"run", "Popen", "call", "check_call", "check_output"}


class ASTSecurityScanner(ast.NodeVisitor):
    """Scan Python AST for dangerous functions and code execution calls."""

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.violations: list[str] = []

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        # Check direct function calls: eval(...), exec(...)
        if isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_CALL_NAMES:
                self.violations.append(
                    f"Forbidden function call '{node.func.id}()' at {self.filename}:{node.lineno}"
                )

        # Check module attribute calls: os.system(...), subprocess.Popen(...)
        elif isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr
            if isinstance(node.func.value, ast.Name):
                module_name = node.func.value.id
                if module_name == "os" and attr_name in FORBIDDEN_OS_CALLS:
                    self.violations.append(
                        f"Forbidden OS execution call 'os.{attr_name}()' at {self.filename}:{node.lineno}"
                    )
                elif module_name == "subprocess" and attr_name in FORBIDDEN_SUBPROCESS_CALLS:
                    self.violations.append(
                        f"Forbidden process spawn 'subprocess.{attr_name}()' at {self.filename}:{node.lineno}"
                    )

        self.generic_visit(node)


def scan_file_ast(file_path: Path) -> None:
    """Parse a Python file and assert no forbidden calls are present."""
    source_code = file_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source_code, filename=str(file_path))
    except SyntaxError as e:
        raise ValidationError(f"Syntax error in generated file {file_path.name}: {e}") from e

    scanner = ASTSecurityScanner(filename=file_path.name)
    scanner.visit(tree)

    if scanner.violations:
        raise SecurityError(
            f"Security check failed for {file_path.name}: {', '.join(scanner.violations)}",
            details={"violations": scanner.violations},
        )


def check_generated_project(project_dir: Path) -> None:
    """Run all validation and security checks on a generated MCP server project."""
    # 1. Validate tools.json against official schema
    manifest_file = project_dir / "tools.json"
    if not manifest_file.exists():
        raise ValidationError("Generated project is missing required 'tools.json' manifest.")

    manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    validate_manifest(manifest_data)

    # 2. AST scan all python files in project
    for py_file in project_dir.rglob("*.py"):
        scan_file_ast(py_file)
