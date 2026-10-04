"""Static analysis: index existing pytest-bdd steps and driver methods via AST."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

STEP_KEYWORDS = {"given", "when", "then"}


@dataclass(frozen=True)
class StepDef:
    keyword: str
    pattern: str
    function: str
    file: str


@dataclass(frozen=True)
class MethodInfo:
    owner: str
    name: str
    signature: str
    doc: str
    file: str

    @property
    def qualified(self) -> str:
        return f"{self.owner}.{self.name}"


def _pattern_from(node: ast.expr) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Call) and node.args:  # parsers.parse("...")
        return _pattern_from(node.args[0])
    return None


def index_steps(root: Path) -> list[StepDef]:
    """Find every @given/@when/@then definition under ``root``."""
    found: list[StepDef] = []
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for deco in node.decorator_list:
                if (
                    isinstance(deco, ast.Call)
                    and isinstance(deco.func, ast.Name)
                    and deco.func.id in STEP_KEYWORDS
                    and deco.args
                ):
                    pattern = _pattern_from(deco.args[0])
                    if pattern:
                        found.append(
                            StepDef(deco.func.id, pattern, node.name, str(path))
                        )
    return found


def index_methods(root: Path) -> list[MethodInfo]:
    """Index public methods of classes (POMs, API clients, drivers)."""
    found: list[MethodInfo] = []
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
            for node in cls.body:
                if not isinstance(node, ast.FunctionDef) or node.name.startswith("_"):
                    continue
                args = ast.unparse(node.args)
                args = args.removeprefix("self, ").removeprefix("self")
                returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
                doc = (ast.get_docstring(node) or "").splitlines()
                found.append(
                    MethodInfo(
                        cls.name,
                        node.name,
                        f"({args}){returns}",
                        doc[0] if doc else "",
                        str(path),
                    )
                )
    return found
