from __future__ import annotations

import ast
import re
from pathlib import Path

from .config import Settings
from .models import ConfigKey, Location, ScanReport


_JS_EXTENSIONS = {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"}
_JAVA_EXTENSIONS = {".java", ".kt"}
_ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
_VARIATION_CALL = re.compile(
    r"\b(?P<receiver>[A-Za-z_$][\w$]*)\.variation\(\s*['\"](?P<name>[A-Za-z0-9_.:-]+)['\"]"
)
_JS_DESTRUCTURE = re.compile(r"\b(?:const|let|var)\s*\{(?P<body>[^}]+)\}\s*=\s*process\.env\b")
_GO_STRING_ASSIGN = re.compile(
    r"\b(?:const\s+)?(?P<variable>[A-Za-z_][A-Za-z0-9_]*)\s*(?::=|=)\s*['\"](?P<value>[A-Z][A-Z0-9_]*)['\"]"
)
_GO_ENV_VAR = re.compile(r"os\.(?:Getenv|LookupEnv)\(\s*(?P<variable>[A-Za-z_][A-Za-z0-9_]*)\s*\)")
_SPRING_VALUE = re.compile(r"@Value\(\s*['\"]\$\{(?P<name>[^}:]+)(?::[^}]*)?\}['\"]\s*\)")

_PACKAGE_JSON_METADATA = {
    "name",
    "version",
    "description",
    "scripts",
    "main",
    "module",
    "type",
    "types",
    "typings",
    "exports",
    "files",
    "bin",
    "engines",
    "dependencies",
    "devDependencies",
    "peerDependencies",
    "optionalDependencies",
    "bundledDependencies",
    "keywords",
    "author",
    "contributors",
    "license",
    "repository",
    "bugs",
    "homepage",
    "packageManager",
    "workspaces",
    "sideEffects",
    "private",
}


def _append_unique(locations: list[Location], location: Location) -> None:
    if not any(
        existing.path == location.path
        and existing.line == location.line
        and existing.kind == location.kind
        and existing.detail == location.detail
        for existing in locations
    ):
        locations.append(location)


def _item(report: ScanReport, name: str, *, language: str, category: str) -> ConfigKey:
    key = report.keys.setdefault(name, ConfigKey(name=name))
    key.languages.add(language)
    key.categories.add(category)
    return key


def _record_env(report: ScanReport, name: str, rel: str, line: int, language: str, is_test: bool, detail: str) -> None:
    if not _ENV_NAME.match(name):
        return
    key = _item(report, name, language=language, category="env")
    location = Location(rel, line, "test" if is_test else "read", detail)
    _append_unique(key.test_mentions if is_test else key.reads, location)


class _PythonStaticEnvVisitor(ast.NodeVisitor):
    def __init__(self, report: ScanReport, rel: str, is_test: bool):
        self.report = report
        self.rel = rel
        self.is_test = is_test
        self.bindings: list[dict[str, str]] = [{}]

    @property
    def scope(self) -> dict[str, str]:
        return self.bindings[-1]

    def _static_string(self, node: ast.AST | None) -> str | None:
        if node is None:
            return None
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Name):
            return self.scope.get(node.id)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left = self._static_string(node.left)
            right = self._static_string(node.right)
            if left is not None and right is not None:
                return left + right
        if isinstance(node, ast.JoinedStr):
            parts: list[str] = []
            for value in node.values:
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    parts.append(value.value)
                elif isinstance(value, ast.FormattedValue):
                    resolved = self._static_string(value.value)
                    if resolved is None:
                        return None
                    parts.append(resolved)
                else:
                    return None
            return "".join(parts)
        return None

    @staticmethod
    def _dotted(node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            left = _PythonStaticEnvVisitor._dotted(node.value)
            return f"{left}.{node.attr}" if left else node.attr
        return ""

    def visit_Assign(self, node: ast.Assign) -> None:
        value = self._static_string(node.value)
        if value is not None:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.scope[target.id] = value
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        value = self._static_string(node.value)
        if value is not None and isinstance(node.target, ast.Name):
            self.scope[node.target.id] = value
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.bindings.append(dict(self.scope))
        self.generic_visit(node)
        self.bindings.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.bindings.append(dict(self.scope))
        self.generic_visit(node)
        self.bindings.pop()

    def visit_Call(self, node: ast.Call) -> None:
        dotted = self._dotted(node.func)
        if dotted in {"os.getenv", "os.environ.get", "os.environ.setdefault"} and node.args:
            name = self._static_string(node.args[0])
            if name:
                _record_env(
                    self.report,
                    name,
                    self.rel,
                    getattr(node, "lineno", 1),
                    "python",
                    self.is_test,
                    "python:static-indirection",
                )
        self.generic_visit(node)


def _recover_python_indirection(path: Path, text: str, rel: str, report: ScanReport, is_test: bool) -> None:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return
    _PythonStaticEnvVisitor(report, rel, is_test).visit(tree)


def _recover_js_destructuring(text: str, rel: str, report: ScanReport, is_test: bool) -> None:
    for match in _JS_DESTRUCTURE.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        for raw in match.group("body").split(","):
            token = raw.strip()
            if not token or token.startswith("..."):
                continue
            key_name = token.split(":", 1)[0].split("=", 1)[0].strip()
            if _ENV_NAME.match(key_name):
                _record_env(report, key_name, rel, line, "javascript", is_test, "javascript:env-destructure")


def _recover_go_indirection(text: str, rel: str, report: ScanReport, is_test: bool) -> None:
    assignments: dict[str, list[tuple[int, str]]] = {}
    for match in _GO_STRING_ASSIGN.finditer(text):
        assignments.setdefault(match.group("variable"), []).append((match.start(), match.group("value")))
    for match in _GO_ENV_VAR.finditer(text):
        candidates = [entry for entry in assignments.get(match.group("variable"), []) if entry[0] < match.start()]
        if not candidates:
            continue
        _, name = max(candidates, key=lambda entry: entry[0])
        line = text.count("\n", 0, match.start()) + 1
        _record_env(report, name, rel, line, "go", is_test, "go:static-indirection")


def _looks_like_flag_receiver(receiver: str) -> bool:
    lowered = receiver.lower()
    return lowered in {"client", "ldclient"} or any(token in lowered for token in ("flag", "feature"))


def _remove_spurious_variations(text: str, rel: str, report: ScanReport) -> None:
    for match in _VARIATION_CALL.finditer(text):
        if _looks_like_flag_receiver(match.group("receiver")):
            continue
        name = match.group("name")
        item = report.keys.get(name)
        if item is None or "feature-flag" not in item.categories:
            continue
        line = text.count("\n", 0, match.start()) + 1
        item.reads = [loc for loc in item.reads if not (loc.path == rel and loc.line == line)]
        item.test_mentions = [loc for loc in item.test_mentions if not (loc.path == rel and loc.line == line)]
        item.branches = [loc for loc in item.branches if not (loc.path == rel and loc.line == line)]
        if not (item.reads or item.test_mentions or item.branches):
            item.categories.discard("feature-flag")
            if not item.categories:
                report.keys.pop(name, None)


def _record_spring_value_declarations(text: str, rel: str, report: ScanReport, is_test: bool) -> None:
    if is_test:
        return
    for match in _SPRING_VALUE.finditer(text):
        name = match.group("name")
        key = _item(report, name, language="java", category="spring")
        line = text.count("\n", 0, match.start()) + 1
        _append_unique(key.declarations, Location(rel, line, "declaration", "java:spring:@Value"))


def _strip_project_metadata(report: ScanReport) -> None:
    to_delete: list[str] = []
    for name, item in report.keys.items():
        kept: list[Location] = []
        removed = False
        for loc in item.declarations:
            filename = Path(loc.path).name
            is_package_metadata = filename == "package.json" and (
                name.split(".", 1)[0] in _PACKAGE_JSON_METADATA
            )
            is_pyproject_metadata = filename == "pyproject.toml" and (
                name == "project" or name.startswith("project.") or name == "build-system" or name.startswith("build-system.")
            )
            if is_package_metadata or is_pyproject_metadata:
                removed = True
                continue
            kept.append(loc)
        if removed:
            item.declarations = kept
        if not (item.reads or item.declarations or item.test_mentions or item.branches or item.runtime_observed):
            to_delete.append(name)
    for name in to_delete:
        report.keys.pop(name, None)


def _drop_unproven_branch_domains(report: ScanReport) -> None:
    for item in report.keys.values():
        if not item.branches:
            item.branch_values.clear()


def apply_hardening(root: Path, settings: Settings, report: ScanReport) -> None:
    """Apply conservative precision/recall hardening after built-in adapters.

    The pass recovers only statically provable environment-key indirection and
    removes a small set of known metadata/feature-flag over-detections. It does
    not execute target code and does not invent values.
    """

    for path in sorted(root.rglob("*"), key=lambda p: p.as_posix()):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if settings.ignored(rel):
            continue
        suffix = path.suffix.lower()
        if suffix not in ({".py", ".go"} | _JS_EXTENSIONS | _JAVA_EXTENSIONS):
            continue
        try:
            if path.stat().st_size > settings.max_file_size:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        is_test = settings.is_test(rel)
        if suffix == ".py":
            _recover_python_indirection(path, text, rel, report, is_test)
            _remove_spurious_variations(text, rel, report)
        elif suffix in _JS_EXTENSIONS:
            _recover_js_destructuring(text, rel, report, is_test)
            _remove_spurious_variations(text, rel, report)
        elif suffix == ".go":
            _recover_go_indirection(text, rel, report, is_test)
        elif suffix in _JAVA_EXTENSIONS:
            _record_spring_value_declarations(text, rel, report, is_test)
            _remove_spurious_variations(text, rel, report)

    _strip_project_metadata(report)
    _drop_unproven_branch_domains(report)
