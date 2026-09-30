from __future__ import annotations

import ast
import configparser
import json
import re
import time
import tomllib
from pathlib import Path
from typing import Iterable

from .baseline import apply_baseline, baseline_path
from .cache import load_cache, repository_fingerprint, save_cache
from .config import Settings, load_settings
from .models import ConfigKey, Location, ScanReport, is_sensitive
from .plugins import load_adapters


TEXT_EXTENSIONS = {
    ".py", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".go", ".java", ".kt", ".rs", ".rb", ".php",
    ".sh", ".bash", ".zsh", ".yaml", ".yml", ".json", ".toml", ".ini", ".cfg",
    ".conf", ".properties", ".tf", ".env", ".example", ".template", ".mk",
}
TEXT_NAMES = {"Dockerfile", "Containerfile", "Makefile", "Procfile", "action.yml", "action.yaml"}
PACKAGE_MARKERS = {"pyproject.toml", "package.json", "go.mod", "Cargo.toml", "pom.xml", "build.gradle", "build.gradle.kts"}

GENERIC_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("javascript", re.compile(r"process\.env(?:\.([A-Z][A-Z0-9_]+)|\[['\"]([A-Z][A-Z0-9_]+)['\"]\])"), "env"),
    ("javascript", re.compile(r"(?:Deno\.env\.get|Bun\.env\.)\(?\s*['\"]?([A-Z][A-Z0-9_]*)['\"]?\s*\)?"), "env"),
    ("go", re.compile(r"os\.(?:Getenv|LookupEnv)\(\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\s*\)"), "env"),
    ("java", re.compile(r"System\.(?:getenv|getProperty)\(\s*['\"]([A-Za-z_][A-Za-z0-9_.-]*)['\"]\s*\)"), "env"),
    ("rust", re.compile(r"(?:std::)?env::var(?:_os)?\(\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\s*\)"), "env"),
    ("ruby", re.compile(r"ENV(?:\[['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\]|\.fetch\(\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\s*\))"), "env"),
    ("php", re.compile(r"""(?<![A-Za-z0-9_.])(?:getenv|env)\(\s*['"]([A-Za-z_][A-Za-z0-9_]*)['"]\s*\)"""), "env"),
    ("shell", re.compile(r"\$\{([A-Z][A-Z0-9_]*)\}|\$([A-Z][A-Z0-9_]*)"), "env"),
]

FEATURE_FLAG_PATTERNS = [
    re.compile(r"(?:isFeatureEnabled|feature_enabled|is_enabled|flag_enabled)\(\s*['\"]([A-Za-z0-9_.:-]+)['\"]"),
    re.compile(r"\.variation\(\s*['\"]([A-Za-z0-9_.:-]+)['\"]"),
]

GITHUB_VALUE_PATTERN = re.compile(r"\$\{\{\s*(vars|secrets)\.([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")

TEST_VALUE_PATTERNS = [
    re.compile(r"(?:setenv|set_env|setEnv)\(\s*['\"](?P<key>[A-Za-z_][A-Za-z0-9_.:-]*)['\"]\s*,\s*(?P<value>['\"][^'\"]*['\"]|True|False|true|false|-?\d+(?:\.\d+)?)"),
    re.compile(r"(?:os\.environ|process\.env)(?:\[['\"](?P<key>[A-Za-z_][A-Za-z0-9_]*)['\"]\]|\.(?P<key2>[A-Z][A-Z0-9_]+))\s*=\s*(?P<value>['\"][^'\"]*['\"]|True|False|true|false|-?\d+(?:\.\d+)?)"),
]

GLOBAL_ENV_OVERWRITE = re.compile(r"(?:os\.environ\.(?:clear|update)|patch\.dict\(\s*os\.environ[^\n]*clear\s*=\s*True)")


def _safe_value(name: str, value: object) -> str:
    if value is None:
        return "<none>"
    if is_sensitive(name):
        return "<set>"
    text = str(value)
    return text if len(text) <= 120 else text[:117] + "..."


def _clean_test_value(name: str, raw: str) -> str:
    raw = raw.strip()
    if (raw.startswith("'") and raw.endswith("'")) or (raw.startswith('"') and raw.endswith('"')):
        raw = raw[1:-1]
    return _safe_value(name, raw.lower() if raw in {"True", "False", "true", "false"} else raw)


def _literal(node: ast.AST | None) -> object | None:
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError):
        return None


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _item(keys: dict[str, ConfigKey], name: str, *, language: str | None = None, category: str | None = None) -> ConfigKey:
    key = keys.setdefault(name, ConfigKey(name=name))
    if language:
        key.languages.add(language)
    if category:
        key.categories.add(category)
    return key


class PythonVisitor(ast.NodeVisitor):
    def __init__(self, rel: str, is_test: bool, keys: dict[str, ConfigKey]):
        self.rel = rel
        self.is_test = is_test
        self.keys = keys
        self.class_stack: list[tuple[str, str | None]] = []
        self.binding_stack: list[dict[str, str]] = [{}]
        self.function_stack: list[str] = []
        self.enum_domains: dict[str, set[str]] = {}

    def item(self, name: str) -> ConfigKey:
        return _item(self.keys, name, language="python")

    def _record_read(self, name: str, node: ast.AST, default: object | None = None, category: str = "env") -> None:
        key = self.item(name)
        key.categories.add(category)
        detail = f"python:{self.function_stack[-1]}" if self.function_stack else "python:module"
        loc = Location(self.rel, getattr(node, "lineno", 1), "test" if self.is_test else "read", detail)
        if self.is_test:
            key.test_mentions.append(loc)
        else:
            key.reads.append(loc)
        if default is not None:
            key.defaults.add(_safe_value(name, default))

    @property
    def bindings(self) -> dict[str, str]:
        return self.binding_stack[-1]

    def _scenario(self) -> str:
        return f"{self.rel}::{self.function_stack[-1]}" if self.function_stack else self.rel

    def _record_test_value(self, key: ConfigKey, value: object, node: ast.AST, detail: str) -> None:
        safe = _safe_value(key.name, value)
        key.tested_values.add(safe)
        key.test_value_observations.setdefault(self._scenario(), set()).add(safe)
        key.test_mentions.append(Location(self.rel, getattr(node, "lineno", 1), "test", detail))

    def _annotation_domain(self, node: ast.AST | None) -> set[str]:
        if node is None:
            return set()
        dotted = self._dotted(node)
        if dotted in {"bool", "builtins.bool"}:
            return {"true", "false"}
        if isinstance(node, ast.Subscript):
            base = self._dotted(node.value)
            if base.endswith("Literal"):
                values = node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
                out = set()
                for value_node in values:
                    value = _literal(value_node)
                    if value is not None:
                        out.add(str(value).lower() if isinstance(value, bool) else str(value))
                return out
        if dotted in self.enum_domains:
            return set(self.enum_domains[dotted])
        return set()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.binding_stack.append({})
        self.function_stack.append(node.name)
        self.generic_visit(node)
        self.function_stack.pop()
        self.binding_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.binding_stack.append({})
        self.function_stack.append(node.name)
        self.generic_visit(node)
        self.function_stack.pop()
        self.binding_stack.pop()

    def visit_Assign(self, node: ast.Assign) -> None:
        if self.is_test:
            assigned = _literal(node.value)
            for target in node.targets:
                if isinstance(target, ast.Subscript) and self._dotted(target.value) == "os.environ":
                    key_name = _literal(target.slice)
                    if isinstance(key_name, str) and assigned is not None:
                        key = self.item(key_name)
                        key.categories.add("env")
                        self._record_test_value(key, assigned, node, "os.environ assignment")
        name = self._env_name_from_expr(node.value)
        if name:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.bindings[target.id] = name
        if self.class_stack and self.class_stack[-1][1]:
            class_name, kind = self.class_stack[-1]
            value = _literal(node.value)
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    key_name = target.id.upper()
                    key = self.item(key_name)
                    key.categories.update({"settings", kind or "config-class"})
                    key.declarations.append(Location(self.rel, getattr(node, "lineno", 1), "declaration", f"{kind}:{class_name}.{target.id}"))
                    if value is not None:
                        if is_sensitive(key_name) and str(value):
                            key.sensitive_default_present = True
                        key.defaults.add(_safe_value(key_name, value))
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        base_names = {self._dotted(base) for base in node.bases}
        if any(name.endswith(("Enum", "StrEnum", "IntEnum")) for name in base_names):
            values: set[str] = set()
            for child in node.body:
                value_node = child.value if isinstance(child, (ast.Assign, ast.AnnAssign)) else None
                value = _literal(value_node)
                if value is not None:
                    values.add(str(value).lower() if isinstance(value, bool) else str(value))
            if values:
                self.enum_domains[node.name] = values
        is_pydantic = any(name.endswith("BaseSettings") for name in base_names)
        is_generic = node.name.lower().endswith(("settings", "config", "configuration"))
        kind = "pydantic" if is_pydantic else ("config-class" if is_generic else None)
        self.class_stack.append((node.name, kind))
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if self.class_stack and self.class_stack[-1][1] and isinstance(node.target, ast.Name):
            class_name, kind = self.class_stack[-1]
            field_name = node.target.id
            name = field_name.upper()
            if isinstance(node.value, ast.Call):
                for kw in node.value.keywords:
                    if kw.arg in {"validation_alias", "alias"}:
                        alias = _literal(kw.value)
                        if isinstance(alias, str):
                            name = alias
            key = self.item(name)
            key.categories.update({"settings", kind or "config-class"})
            key.declarations.append(Location(self.rel, getattr(node, "lineno", 1), "declaration", f"{kind}:{class_name}.{field_name}"))
            domain = self._annotation_domain(node.annotation)
            if domain:
                key.expected_values.update(_safe_value(name, value) for value in domain)
                if {value.lower() for value in domain} >= {"true", "false"}:
                    key.branch_values.update({"true", "false"})
                key.validators.add("annotation-domain")
            default = _literal(node.value)
            if default is not None:
                if is_sensitive(name) and str(default):
                    key.sensitive_default_present = True
                key.defaults.add(_safe_value(name, default))
            if isinstance(node.value, ast.Call):
                for kw in node.value.keywords:
                    if kw.arg in {"pattern", "regex", "ge", "gt", "le", "lt", "min_length", "max_length"}:
                        val = _literal(kw.value)
                        key.validators.add(f"{kw.arg}={val if val is not None else '<dynamic>'}")
        if isinstance(node.target, ast.Name) and node.value is not None:
            bound = self._env_name_from_expr(node.value)
            if bound:
                self.bindings[node.target.id] = bound
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        dotted = self._dotted(func)
        if dotted in {"os.getenv", "os.environ.get", "os.environ.setdefault"} and node.args:
            name = _literal(node.args[0])
            if isinstance(name, str):
                default = _literal(node.args[1]) if len(node.args) > 1 else None
                self._record_read(name, node, default)

        if isinstance(func, ast.Attribute) and func.attr == "add_argument" and node.args:
            self._record_cli_call(node)
        elif dotted in {"click.option", "typer.Option"} and node.args:
            self._record_cli_call(node)

        if isinstance(func, ast.Attribute) and dotted.endswith("monkeypatch.setenv") and len(node.args) >= 2:
            name, value = _literal(node.args[0]), _literal(node.args[1])
            if isinstance(name, str):
                key = self.item(name)
                key.categories.add("env")
                if value is not None:
                    self._record_test_value(key, value, node, "monkeypatch.setenv")
                else:
                    key.test_mentions.append(Location(self.rel, getattr(node, "lineno", 1), "test", "monkeypatch.setenv"))

        call_name = dotted.split(".")[-1]
        if call_name in {"is_enabled", "feature_enabled", "flag_enabled", "isFeatureEnabled", "variation"} and node.args:
            name = _literal(node.args[0])
            if isinstance(name, str):
                self._record_read(name, node, category="feature-flag")
                flag = self.item(name)
                flag.expected_values.update({"true", "false"})
                flag.branch_values.update({"true", "false"})
                if not self.is_test:
                    flag.branches.append(Location(self.rel, getattr(node, "lineno", 1), "branch", "feature-flag:boolean"))

        self.generic_visit(node)

    def _record_cli_call(self, node: ast.Call) -> None:
        flag = _literal(node.args[0]) if node.args else None
        if not isinstance(flag, str) or not flag.startswith("--"):
            return
        name = flag[2:].replace("-", "_").upper()
        key = self.item(name)
        key.categories.add("cli")
        loc = Location(self.rel, getattr(node, "lineno", 1), "test" if self.is_test else "declaration", flag)
        (key.test_mentions if self.is_test else key.declarations).append(loc)
        for kw in node.keywords:
            if kw.arg == "default":
                val = _literal(kw.value)
                if val is not None:
                    key.defaults.add(_safe_value(name, val))
            if kw.arg == "choices":
                vals = _literal(kw.value)
                if isinstance(vals, (list, tuple, set)):
                    key.expected_values.update(_safe_value(name, x) for x in vals)
            if kw.arg == "action":
                val = _literal(kw.value)
                if val in {"store_true", "store_false"}:
                    key.expected_values.update({"true", "false"})

    def visit_Subscript(self, node: ast.Subscript) -> None:
        if self._dotted(node.value) == "os.environ":
            name = _literal(node.slice)
            if isinstance(name, str):
                self._record_read(name, node)
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        name = self._env_name_from_expr(node.left)
        if name and node.comparators:
            for comparator in node.comparators:
                value = _literal(comparator)
                if value is not None:
                    safe = _safe_value(name, value)
                    key = self.item(name)
                    key.expected_values.add(safe)
                    key.branch_values.add(safe)
                    if not self.is_test:
                        op = type(node.ops[0]).__name__ if node.ops else "Compare"
                        key.branches.append(Location(self.rel, getattr(node, "lineno", 1), "branch", f"{op}:{safe}"))
        self.generic_visit(node)

    def _env_name_from_expr(self, node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return self.bindings.get(node.id)
        if isinstance(node, ast.Call):
            dotted = self._dotted(node.func)
            if dotted in {"os.getenv", "os.environ.get"} and node.args:
                value = _literal(node.args[0])
                return value if isinstance(value, str) else None
            if isinstance(node.func, ast.Attribute) and node.func.attr in {"lower", "casefold", "strip"}:
                return self._env_name_from_expr(node.func.value)
        if isinstance(node, ast.Subscript) and self._dotted(node.value) == "os.environ":
            value = _literal(node.slice)
            return value if isinstance(value, str) else None
        return None

    @staticmethod
    def _dotted(node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            left = PythonVisitor._dotted(node.value)
            return f"{left}.{node.attr}" if left else node.attr
        return ""


def _record_generic(text: str, rel: str, is_test: bool, keys: dict[str, ConfigKey]) -> None:
    for language, pattern, category in GENERIC_PATTERNS:
        for match in pattern.finditer(text):
            name = next((g for g in match.groups() if g), None)
            if not name:
                continue
            key = _item(keys, name, language=language, category=category)
            loc = Location(rel, _line_number(text, match.start()), "test" if is_test else "read", language)
            (key.test_mentions if is_test else key.reads).append(loc)

    for pattern in FEATURE_FLAG_PATTERNS:
        for match in pattern.finditer(text):
            name = match.group(1)
            key = _item(keys, name, category="feature-flag")
            key.expected_values.update({"true", "false"})
            key.branch_values.update({"true", "false"})
            loc = Location(rel, _line_number(text, match.start()), "test" if is_test else "read", "feature-flag")
            (key.test_mentions if is_test else key.reads).append(loc)

    for match in GITHUB_VALUE_PATTERN.finditer(text):
        kind, name = match.groups()
        key = _item(keys, name, language="github-actions", category="secret" if kind == "secrets" else "actions-var")
        key.declarations.append(Location(rel, _line_number(text, match.start()), "declaration", f"github-{kind}"))

    if is_test and not rel.endswith(".py"):
        for pattern in TEST_VALUE_PATTERNS:
            for match in pattern.finditer(text):
                gd = match.groupdict()
                name = gd.get("key") or gd.get("key2")
                value = gd.get("value")
                if not name:
                    continue
                key = keys.setdefault(name, ConfigKey(name=name))
                key.test_mentions.append(Location(rel, _line_number(text, match.start()), "test", "assignment"))
                if value is not None:
                    clean = _clean_test_value(name, value)
                    key.tested_values.add(clean)
                    key.test_value_observations.setdefault(rel, set()).add(clean)


def _record_env_file(text: str, rel: str, keys: dict[str, ConfigKey]) -> None:
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
        if not match:
            continue
        name, value = match.groups()
        key = _item(keys, name, category="env")
        key.declarations.append(Location(rel, lineno, "declaration", "env-file"))
        if value:
            if is_sensitive(name):
                key.sensitive_default_present = True
            key.defaults.add(_safe_value(name, value.strip('"\'')))


def _flatten(prefix: str, obj: object) -> Iterable[tuple[str, object]]:
    if isinstance(obj, dict):
        for key, value in obj.items():
            dotted = f"{prefix}.{key}" if prefix else str(key)
            yield from _flatten(dotted, value)
    elif isinstance(obj, list):
        yield prefix, f"<list:{len(obj)}>"
    elif prefix:
        yield prefix, obj


def _record_structured(path: Path, text: str, rel: str, keys: dict[str, ConfigKey]) -> None:
    suffix = path.suffix.lower()
    data: object | None = None
    try:
        if suffix == ".json":
            data = json.loads(text)
        elif suffix == ".toml":
            data = tomllib.loads(text)
        elif suffix in {".ini", ".cfg"}:
            parser = configparser.ConfigParser()
            parser.read_string(text)
            data = {section: dict(parser[section]) for section in parser.sections()}
    except Exception:
        data = None
    if data is not None:
        for name, value in _flatten("", data):
            key = _item(keys, name, category="settings")
            key.declarations.append(Location(rel, 1, "declaration", suffix.lstrip(".")))
            if not isinstance(value, (dict, list)):
                if is_sensitive(name) and str(value):
                    key.sensitive_default_present = True
                key.defaults.add(_safe_value(name, value))


def _record_properties(text: str, rel: str, keys: dict[str, ConfigKey]) -> None:
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith(("#", "!")):
            continue
        match = re.match(r"([^:=\s][^:=]*?)\s*[:=]\s*(.*)$", line)
        if not match:
            continue
        name, value = match.groups()
        name = name.strip()
        key = _item(keys, name, category="settings")
        key.declarations.append(Location(rel, lineno, "declaration", "properties"))
        if value:
            if is_sensitive(name):
                key.sensitive_default_present = True
            key.defaults.add(_safe_value(name, value.strip()))


def _record_yaml(text: str, rel: str, keys: dict[str, ConfigKey], *, helm: bool = False) -> None:
    lines = text.splitlines()
    stack: list[tuple[int, str]] = []
    for idx, raw in enumerate(lines, 1):
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        list_env = re.match(r"^\s*-\s*([A-Z][A-Z0-9_]*)=(.*?)\s*$", line)
        if list_env:
            name, value = list_env.groups()
            key = _item(keys, name, category="deployment")
            key.declarations.append(Location(rel, idx, "declaration", "yaml-env"))
            if value:
                if is_sensitive(name):
                    key.sensitive_default_present = True
                key.defaults.add(_safe_value(name, value.strip('"\'')))
        name_match = re.match(r"^\s*-?\s*name:\s*([A-Z][A-Z0-9_]{1,})\s*$", line)
        if name_match:
            name = name_match.group(1)
            key = _item(keys, name, category="deployment")
            key.declarations.append(Location(rel, idx, "declaration", "yaml-env"))
        match = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_.-]*)\s*:\s*(.*?)\s*$", line)
        if not match:
            continue
        name, value = match.groups()
        while stack and stack[-1][0] >= indent:
            stack.pop()
        if not value:
            stack.append((indent, name))
        dotted = ".".join([part for _, part in stack] + ([name] if value else []))
        if name.isupper() and len(name) >= 2:
            key = _item(keys, name, category="deployment")
            key.declarations.append(Location(rel, idx, "declaration", "yaml"))
            if value and value not in {"|", ">", "{}", "[]"}:
                if is_sensitive(name):
                    key.sensitive_default_present = True
                key.defaults.add(_safe_value(name, value.strip('"\'')))
        elif helm and value and dotted:
            key = _item(keys, dotted, category="helm")
            key.declarations.append(Location(rel, idx, "declaration", "helm-values"))
            key.defaults.add(_safe_value(dotted, value.strip('"\'')))


def _record_terraform(text: str, rel: str, keys: dict[str, ConfigKey]) -> None:
    for match in re.finditer(r'variable\s+"([A-Za-z_][A-Za-z0-9_-]*)"\s*\{(?P<body>.*?)\n\}', text, re.S):
        name = match.group(1)
        body = match.group("body")
        key = _item(keys, name, category="terraform")
        key.declarations.append(Location(rel, _line_number(text, match.start()), "declaration", "terraform"))
        default_match = re.search(r"\bdefault\s*=\s*([^\n]+)", body)
        if default_match:
            raw_default = default_match.group(1).strip().strip('"\'')
            if is_sensitive(name) and raw_default:
                key.sensitive_default_present = True
            key.defaults.add(_safe_value(name, raw_default))
        validation = re.search(r"\bvalidation\s*\{", body)
        if validation:
            key.validators.add("terraform-validation")


def _record_makefile(text: str, rel: str, keys: dict[str, ConfigKey]) -> None:
    for lineno, line in enumerate(text.splitlines(), 1):
        match = re.match(r"^([A-Z][A-Z0-9_]{2,})\s*(?:\?=|:=|=)\s*(.*)$", line)
        if match:
            name, value = match.groups()
            key = _item(keys, name, category="make")
            key.declarations.append(Location(rel, lineno, "declaration", "make"))
            if value:
                if is_sensitive(name):
                    key.sensitive_default_present = True
                key.defaults.add(_safe_value(name, value))


def _record_dockerfile(text: str, rel: str, keys: dict[str, ConfigKey]) -> None:
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        arg = re.match(r"ARG\s+([A-Za-z_][A-Za-z0-9_]*)(?:=(.*))?$", line, re.I)
        env = re.match(r"ENV\s+([A-Za-z_][A-Za-z0-9_]*)[=\s]+(.*)$", line, re.I)
        match = arg or env
        if not match:
            continue
        name, value = match.groups()
        key = _item(keys, name, category="docker")
        key.declarations.append(Location(rel, lineno, "declaration", "docker-arg" if arg else "docker-env"))
        if value:
            if is_sensitive(name):
                key.sensitive_default_present = True
            key.defaults.add(_safe_value(name, value.strip()))


def _eligible(path: Path) -> bool:
    if path.name.startswith(".env"):
        return True
    if path.name in TEXT_NAMES:
        return True
    return path.suffix.lower() in TEXT_EXTENSIONS


def _package_roots(root: Path, files: list[Path]) -> list[str]:
    roots = set()
    for path in files:
        if path.name in PACKAGE_MARKERS:
            rel = path.parent.relative_to(root).as_posix()
            roots.add("." if rel == "." else rel)
    return sorted(roots)


def _apply_trace(root: Path, configured: str, keys: dict[str, ConfigKey]) -> None:
    path = Path(configured)
    path = path if path.is_absolute() else root / path
    if not path.exists():
        return
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for line in lines:
        try:
            data = json.loads(line)
            name = data["key"]
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
        if isinstance(name, str):
            key = keys.setdefault(name, ConfigKey(name=name))
            key.runtime_observed = True
            key.categories.add("runtime-trace")


def _infer_boolean_domains(keys: dict[str, ConfigKey]) -> None:
    bool_values = {"true", "false"}
    for item in keys.values():
        expected_lower = {x.lower() for x in item.expected_values}
        defaults_lower = {x.lower() for x in item.defaults}
        if expected_lower & bool_values or defaults_lower & bool_values or "feature-flag" in item.categories:
            item.expected_values.update(bool_values)


def scan(root: str | Path = ".", settings: Settings | None = None, *, use_cache: bool | None = None) -> ScanReport:
    started = time.perf_counter()
    root_path = Path(root).resolve()
    settings = settings or load_settings(root_path)
    cache_enabled = settings.cache if use_cache is None else use_cache

    files: list[Path] = []
    for path in root_path.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root_path).as_posix()
        if settings.ignored(rel) or not _eligible(path):
            continue
        files.append(path)
    files.sort(key=lambda p: p.relative_to(root_path).as_posix())

    config_path = root_path / "configreach.toml"
    config_bytes = config_path.read_bytes() if config_path.exists() else b""
    trace_path = Path(settings.trace_file)
    trace_path = trace_path if trace_path.is_absolute() else root_path / trace_path
    if trace_path.exists():
        try:
            st = trace_path.stat()
            config_bytes += f"trace:{st.st_size}:{st.st_mtime_ns}".encode()
        except OSError:
            pass
    fingerprint = repository_fingerprint(root_path, files, config_bytes)

    if cache_enabled:
        cached = load_cache(root_path, fingerprint)
        if cached is not None:
            for item in cached.keys.values():
                item.baseline_ignored = False
            apply_baseline(cached, baseline_path(root_path, settings.baseline))
            cached.scan_seconds = time.perf_counter() - started
            return cached

    keys: dict[str, ConfigKey] = {}
    files_scanned = 0
    tests_scanned = 0
    warnings: list[str] = []
    test_files: list[tuple[str, str]] = []
    test_global_overwrites: list[Location] = []
    adapters, plugin_warnings = load_adapters() if settings.plugins else ([], [])
    warnings.extend(plugin_warnings)

    for path in files:
        rel = path.relative_to(root_path).as_posix()
        try:
            if path.stat().st_size > settings.max_file_size:
                warnings.append(f"Skipped large file: {rel}")
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            warnings.append(f"Could not read {rel}: {exc}")
            continue

        files_scanned += 1
        is_test = settings.is_test(rel)
        tests_scanned += int(is_test)
        if is_test:
            test_files.append((rel, text))
            for overwrite in GLOBAL_ENV_OVERWRITE.finditer(text):
                test_global_overwrites.append(Location(rel, _line_number(text, overwrite.start()), "test", "global-environment-overwrite"))

        if path.suffix.lower() == ".py":
            try:
                tree = ast.parse(text, filename=rel)
                PythonVisitor(rel, is_test, keys).visit(tree)
            except SyntaxError:
                warnings.append(f"Python parse failed: {rel}")

        _record_generic(text, rel, is_test, keys)
        lower_name = path.name.lower()
        if lower_name.startswith(".env") or lower_name.endswith((".example", ".template")):
            _record_env_file(text, rel, keys)
        if path.suffix.lower() in {".json", ".toml", ".ini", ".cfg"} and path.name != "configreach.toml":
            _record_structured(path, text, rel, keys)
        if path.suffix.lower() == ".properties":
            _record_properties(text, rel, keys)
        if path.suffix.lower() in {".yaml", ".yml"}:
            helm = lower_name in {"values.yaml", "values.yml"} or "/charts/" in f"/{rel.lower()}/"
            _record_yaml(text, rel, keys, helm=helm)
        if path.suffix.lower() == ".tf":
            _record_terraform(text, rel, keys)
        if path.name == "Makefile" or path.suffix.lower() == ".mk":
            _record_makefile(text, rel, keys)
        if path.name in {"Dockerfile", "Containerfile"} or lower_name.startswith("dockerfile"):
            _record_dockerfile(text, rel, keys)

        for loaded in adapters:
            try:
                if loaded.adapter.supports(path):
                    loaded.adapter.scan(path=path, rel=rel, text=text, is_test=is_test, keys=keys)
            except Exception as exc:
                warnings.append(f"Plugin {loaded.name!r} failed on {rel}: {exc}")

    for name, key in keys.items():
        if key.test_mentions:
            continue
        token = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])")
        for rel, text in test_files:
            match = token.search(text)
            if match:
                key.test_mentions.append(Location(rel, _line_number(text, match.start()), "test", "name-reference"))
                break

    _apply_trace(root_path, settings.trace_file, keys)
    _infer_boolean_domains(keys)
    report = ScanReport(
        str(root_path), keys, files_scanned, tests_scanned, warnings,
        scan_seconds=time.perf_counter() - started,
        package_roots=_package_roots(root_path, files),
        test_global_overwrites=test_global_overwrites,
    )
    apply_baseline(report, baseline_path(root_path, settings.baseline))

    if cache_enabled:
        for item in report.keys.values():
            item.baseline_ignored = False
        save_cache(root_path, fingerprint, report)
        apply_baseline(report, baseline_path(root_path, settings.baseline))
    report.scan_seconds = time.perf_counter() - started
    return report
