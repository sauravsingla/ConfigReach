from __future__ import annotations

import re
from pathlib import Path

from .config import Settings
from .models import ConfigKey, Location, ScanReport

_JS_EXTENSIONS = {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"}
_JAVA_EXTENSIONS = {".java", ".kt"}
_SHELL_EXTENSIONS = {".sh", ".bash", ".zsh"}
_RELEVANT_EXTENSIONS = _JS_EXTENSIONS | _JAVA_EXTENSIONS | _SHELL_EXTENSIONS | {".go", ".cs", ".rs", ".rb", ".php", ".yaml", ".yml"}

_JS_ENV = re.compile(r"process\.env(?:\.([A-Z][A-Z0-9_]*)|\[['\"]([A-Z][A-Z0-9_]*)['\"]\])")
_DENO = re.compile(r"Deno\.env\.get\(\s*['\"]([A-Z][A-Z0-9_]*)['\"]\s*\)")
_BUN = re.compile(r"Bun\.env\.([A-Z][A-Z0-9_]*)")
_JS_DESTRUCTURE = re.compile(r"\b(?:const|let|var)\s*\{(?P<body>[^}]+)\}\s*=\s*process\.env\b")
_JS_FEATURE = re.compile(r"(?:\.isEnabled|\.is_enabled|\.variation|\.getBooleanValue)\(\s*['\"]([A-Za-z0-9_.:-]+)['\"]")
_GO_ENV = re.compile(r"os\.(?:Getenv|LookupEnv)\(\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\s*\)")
_GO_ASSIGN = re.compile(r"\b(?:const\s+)?(?P<variable>[A-Za-z_][A-Za-z0-9_]*)\s*(?::=|=)\s*['\"](?P<value>[A-Z][A-Z0-9_]*)['\"]")
_GO_ENV_VAR = re.compile(r"os\.(?:Getenv|LookupEnv)\(\s*(?P<variable>[A-Za-z_][A-Za-z0-9_]*)\s*\)")
_JAVA_SYS = re.compile(r"System\.(?:getenv|getProperty)\(\s*['\"]([A-Za-z_][A-Za-z0-9_.-]*)['\"]\s*\)")
_SPRING_VALUE = re.compile(r"@Value\(\s*['\"]\$\{([^}:]+)(?::([^}]*))?\}['\"]\s*\)")
_SPRING_GET = re.compile(r"\b(?:environment|env)\.getProperty\(\s*['\"]([^'\"]+)['\"](?:\s*,\s*['\"]([^'\"]*)['\"])?")
_JAVA_FEATURE = re.compile(r"\.(?:isEnabled|variation|getBooleanValue)\(\s*['\"]([A-Za-z0-9_.:-]+)['\"]")
_CS_ENV = re.compile(r"Environment\.GetEnvironmentVariable\(\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\s*\)")
_CS_INDEX = re.compile(r"\b(?:configuration|config|builder\.Configuration)\s*\[\s*['\"]([^'\"]+)['\"]\s*\]")
_CS_GETVALUE = re.compile(r"\.(?:GetValue(?:<[^>]+>)?|GetConnectionString)\(\s*['\"]([^'\"]+)['\"](?:\s*,\s*([^\)]+))?\)")
_CS_FEATURE = re.compile(r"\.IsEnabledAsync?\(\s*['\"]([A-Za-z0-9_.:-]+)['\"]")
_RUST = re.compile(r"(?:std::)?env::var(?:_os)?\(\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\s*\)")
_RUBY = re.compile(r"ENV(?:\[['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\]|\.fetch\(\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\s*\))")
_PHP = re.compile(r"(?<![A-Za-z0-9_.])(?:getenv|env)\(\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\s*\)")
_SHELL = re.compile(r"\$\{([A-Z][A-Z0-9_]*)\}|\$([A-Z][A-Z0-9_]*)")
_GITHUB = re.compile(r"\$\{\{\s*(vars|secrets)\.([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")
_GENERIC_FEATURE = [
    re.compile(r"(?:isFeatureEnabled|feature_enabled|is_enabled|flag_enabled)\(\s*['\"]([A-Za-z0-9_.:-]+)['\"]"),
    re.compile(r"\.variation\(\s*['\"]([A-Za-z0-9_.:-]+)['\"]"),
]


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _match_in_code(mask: list[bool], start: int) -> bool:
    return 0 <= start < len(mask) and mask[start]


def _c_like_code_positions(text: str, *, backtick: bool = False, rust_raw: bool = False) -> list[bool]:
    n = len(text)
    code = [True] * n
    i = 0
    state = "code"
    quote = ""
    raw_hashes = 0
    while i < n:
        if state == "line_comment":
            code[i] = False
            if text[i] == "\n":
                state = "code"
                code[i] = True
            i += 1
            continue
        if state == "block_comment":
            code[i] = False
            if i + 1 < n and text[i : i + 2] == "*/":
                code[i + 1] = False
                i += 2
                state = "code"
            else:
                i += 1
            continue
        if state == "string":
            code[i] = False
            if text[i] == "\\" and quote != "`" and i + 1 < n:
                code[i + 1] = False
                i += 2
                continue
            if text[i] == quote:
                state = "code"
            i += 1
            continue
        if state == "rust_raw":
            code[i] = False
            close = '"' + ("#" * raw_hashes)
            if text.startswith(close, i):
                for j in range(i, min(n, i + len(close))):
                    code[j] = False
                i += len(close)
                state = "code"
            else:
                i += 1
            continue

        if i + 1 < n and text[i : i + 2] == "//":
            code[i] = code[i + 1] = False
            i += 2
            state = "line_comment"
            continue
        if i + 1 < n and text[i : i + 2] == "/*":
            code[i] = code[i + 1] = False
            i += 2
            state = "block_comment"
            continue
        if rust_raw and text[i] == "r":
            match = re.match(r'r(#{0,16})"', text[i:])
            if match:
                raw_hashes = len(match.group(1))
                span = len(match.group(0))
                for j in range(i, min(n, i + span)):
                    code[j] = False
                i += span
                state = "rust_raw"
                continue
        if text[i] in ('"', "'") or (backtick and text[i] == "`"):
            quote = text[i]
            code[i] = False
            i += 1
            state = "string"
            continue
        i += 1
    return code


def _comment_only_code_positions(text: str) -> list[bool]:
    n = len(text)
    active = [True] * n
    i = 0
    quote: str | None = None
    block = False
    while i < n:
        if block:
            active[i] = False
            if i + 1 < n and text[i : i + 2] == "*/":
                active[i + 1] = False
                i += 2
                block = False
            else:
                i += 1
            continue
        ch = text[i]
        if quote is not None:
            if ch == "\\" and i + 1 < n:
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in ('"', "'"):
            quote = ch
            i += 1
            continue
        if i + 1 < n and text[i : i + 2] == "//":
            j = i
            while j < n and text[j] != "\n":
                active[j] = False
                j += 1
            i = j
            continue
        if i + 1 < n and text[i : i + 2] == "/*":
            active[i] = active[i + 1] = False
            i += 2
            block = True
            continue
        i += 1
    return active


def _js_code_positions(text: str) -> list[bool]:
    n = len(text)
    active = [True] * n

    def mask_string(i: int, quote: str) -> int:
        active[i] = False
        i += 1
        while i < n:
            active[i] = False
            if text[i] == "\\" and i + 1 < n:
                active[i + 1] = False
                i += 2
                continue
            if text[i] == quote:
                return i + 1
            i += 1
        return i

    def mask_line_comment(i: int) -> int:
        while i < n and text[i] != "\n":
            active[i] = False
            i += 1
        return i

    def mask_block_comment(i: int) -> int:
        active[i] = False
        if i + 1 < n:
            active[i + 1] = False
        i += 2
        while i < n:
            active[i] = False
            if i + 1 < n and text[i : i + 2] == "*/":
                active[i + 1] = False
                return i + 2
            i += 1
        return i

    def scan_expr(i: int) -> int:
        depth = 1
        while i < n and depth:
            if i + 1 < n and text[i : i + 2] == "//":
                i = mask_line_comment(i)
                continue
            if i + 1 < n and text[i : i + 2] == "/*":
                i = mask_block_comment(i)
                continue
            if text[i] in ('"', "'"):
                i = mask_string(i, text[i])
                continue
            if text[i] == "`":
                i = scan_template(i)
                continue
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    active[i] = False
                    return i + 1
            i += 1
        return i

    def scan_template(i: int) -> int:
        active[i] = False
        i += 1
        while i < n:
            active[i] = False
            if text[i] == "\\" and i + 1 < n:
                active[i + 1] = False
                i += 2
                continue
            if text[i] == "`":
                return i + 1
            if i + 1 < n and text[i : i + 2] == "${":
                active[i] = active[i + 1] = False
                i = scan_expr(i + 2)
                continue
            i += 1
        return i

    i = 0
    while i < n:
        if i + 1 < n and text[i : i + 2] == "//":
            i = mask_line_comment(i)
            continue
        if i + 1 < n and text[i : i + 2] == "/*":
            i = mask_block_comment(i)
            continue
        if text[i] in ('"', "'"):
            i = mask_string(i, text[i])
            continue
        if text[i] == "`":
            i = scan_template(i)
            continue
        i += 1
    return active


def _ruby_code_positions(text: str) -> list[bool]:
    n = len(text)
    active = [True] * n

    def mask_single(i: int) -> int:
        active[i] = False
        i += 1
        while i < n:
            active[i] = False
            if text[i] == "\\" and i + 1 < n:
                active[i + 1] = False
                i += 2
                continue
            if text[i] == "'":
                return i + 1
            i += 1
        return i

    def mask_double(i: int) -> int:
        active[i] = False
        i += 1
        while i < n:
            active[i] = False
            if text[i] == "\\" and i + 1 < n:
                active[i + 1] = False
                i += 2
                continue
            if text[i] == '"':
                return i + 1
            if i + 1 < n and text[i : i + 2] == "#{":
                active[i] = active[i + 1] = False
                i = scan_expr(i + 2)
                continue
            i += 1
        return i

    def scan_expr(i: int) -> int:
        depth = 1
        while i < n and depth:
            if text[i] == "#":
                while i < n and text[i] != "\n":
                    active[i] = False
                    i += 1
                continue
            if text[i] == "'":
                i = mask_single(i)
                continue
            if text[i] == '"':
                i = mask_double(i)
                continue
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    active[i] = False
                    return i + 1
            i += 1
        return i

    i = 0
    while i < n:
        if text[i] == "#":
            while i < n and text[i] != "\n":
                active[i] = False
                i += 1
            continue
        if text[i] == "'":
            i = mask_single(i)
            continue
        if text[i] == '"':
            i = mask_double(i)
            continue
        i += 1
    return active


def _shell_match_active(text: str, start: int) -> bool:
    line_start = text.rfind("\n", 0, start) + 1
    single = double = False
    escaped = False
    i = line_start
    while i < start:
        ch = text[i]
        if escaped:
            escaped = False
            i += 1
            continue
        if ch == "\\" and not single:
            escaped = True
            i += 1
            continue
        if ch == "'" and not double:
            single = not single
            i += 1
            continue
        if ch == '"' and not single:
            double = not double
            i += 1
            continue
        if ch == "#" and not single and not double:
            return False
        i += 1
    return not single


def _yaml_match_active(text: str, start: int) -> bool:
    line_start = text.rfind("\n", 0, start) + 1
    single = double = False
    escaped = False
    i = line_start
    while i < start:
        ch = text[i]
        if escaped:
            escaped = False
            i += 1
            continue
        if ch == "\\" and double:
            escaped = True
            i += 1
            continue
        if ch == "'" and not double:
            single = not single
            i += 1
            continue
        if ch == '"' and not single:
            double = not double
            i += 1
            continue
        if ch == "#" and not single and not double:
            return False
        i += 1
    return True


def _active_key_lines(text: str, suffix: str) -> set[tuple[str, int]]:
    active: set[tuple[str, int]] = set()

    def add_matches(pattern: re.Pattern[str], mask: list[bool], group: int | None = 1) -> None:
        for match in pattern.finditer(text):
            if not _match_in_code(mask, match.start()):
                continue
            if group is None:
                name = next((value for value in match.groups() if value), None)
            else:
                name = match.group(group)
            if name:
                active.add((name, _line_number(text, match.start())))

    if suffix in _JS_EXTENSIONS:
        mask = _js_code_positions(text)
        for pattern in (_JS_ENV, _DENO, _BUN):
            add_matches(pattern, mask, None)
        for match in _JS_DESTRUCTURE.finditer(text):
            if not _match_in_code(mask, match.start()):
                continue
            line = _line_number(text, match.start())
            for raw in match.group("body").split(","):
                token = raw.strip()
                if not token or token.startswith("..."):
                    continue
                name = token.split(":", 1)[0].split("=", 1)[0].strip()
                if re.fullmatch(r"[A-Z][A-Z0-9_]*", name):
                    active.add((name, line))
        add_matches(_JS_FEATURE, mask)
        for pattern in _GENERIC_FEATURE:
            add_matches(pattern, mask)
    elif suffix == ".go":
        mask = _c_like_code_positions(text, backtick=True)
        add_matches(_GO_ENV, mask)
        assignments: dict[str, list[tuple[int, str]]] = {}
        for match in _GO_ASSIGN.finditer(text):
            if _match_in_code(mask, match.start()):
                assignments.setdefault(match.group("variable"), []).append((match.start(), match.group("value")))
        for match in _GO_ENV_VAR.finditer(text):
            if not _match_in_code(mask, match.start()):
                continue
            candidates = [entry for entry in assignments.get(match.group("variable"), []) if entry[0] < match.start()]
            if candidates:
                _, name = max(candidates, key=lambda entry: entry[0])
                active.add((name, _line_number(text, match.start())))
        for pattern in _GENERIC_FEATURE:
            add_matches(pattern, mask)
    elif suffix in _JAVA_EXTENSIONS:
        mask = _comment_only_code_positions(text)
        add_matches(_JAVA_SYS, mask)
        add_matches(_SPRING_VALUE, mask)
        add_matches(_SPRING_GET, mask)
        add_matches(_JAVA_FEATURE, mask)
        for pattern in _GENERIC_FEATURE:
            add_matches(pattern, mask)
    elif suffix == ".cs":
        mask = _comment_only_code_positions(text)
        add_matches(_CS_ENV, mask)
        add_matches(_CS_INDEX, mask)
        add_matches(_CS_GETVALUE, mask)
        add_matches(_CS_FEATURE, mask)
    elif suffix == ".rs":
        mask = _c_like_code_positions(text, rust_raw=True)
        add_matches(_RUST, mask)
        for pattern in _GENERIC_FEATURE:
            add_matches(pattern, mask)
    elif suffix == ".rb":
        mask = _ruby_code_positions(text)
        add_matches(_RUBY, mask, None)
        for pattern in _GENERIC_FEATURE:
            add_matches(pattern, mask)
    elif suffix == ".php":
        mask = _c_like_code_positions(text)
        for match in _PHP.finditer(text):
            if not _match_in_code(mask, match.start()):
                continue
            if text[max(0, match.start() - 2) : match.start()] in {"->", "::"}:
                continue
            active.add((match.group(1), _line_number(text, match.start())))
        for pattern in _GENERIC_FEATURE:
            add_matches(pattern, mask)
    elif suffix in _SHELL_EXTENSIONS:
        for match in _SHELL.finditer(text):
            if _shell_match_active(text, match.start()):
                name = next((value for value in match.groups() if value), None)
                if name:
                    active.add((name, _line_number(text, match.start())))
    elif suffix in {".yaml", ".yml"}:
        for match in _GITHUB.finditer(text):
            if _yaml_match_active(text, match.start()):
                active.add((match.group(2), _line_number(text, match.start())))
    return active


def _pattern_location(location: Location) -> bool:
    detail = location.detail
    return (
        detail in {"javascript", "go", "java", "rust", "ruby", "php", "shell", "feature-flag"}
        or detail.startswith("javascript:")
        or detail.startswith("go:")
        or detail in {"java:spring:@Value", "java:spring:getProperty"}
        or detail == "java:feature-flag"
        or detail.startswith("dotnet:")
        or detail.startswith("github-")
    )


def _filter_locations(locations: list[Location], name: str, rel: str, active: set[tuple[str, int]]) -> list[Location]:
    return [
        loc
        for loc in locations
        if not (loc.path == rel and _pattern_location(loc) and (name, loc.line) not in active)
    ]


def _remove_empty_keys(report: ScanReport) -> None:
    for name in list(report.keys):
        item = report.keys[name]
        if not (item.reads or item.declarations or item.test_mentions or item.branches or item.runtime_observed):
            report.keys.pop(name, None)


def _filter_file(report: ScanReport, rel: str, text: str, suffix: str) -> None:
    active = _active_key_lines(text, suffix)
    for name, item in list(report.keys.items()):
        item.reads = _filter_locations(item.reads, name, rel, active)
        item.test_mentions = _filter_locations(item.test_mentions, name, rel, active)
        item.declarations = _filter_locations(item.declarations, name, rel, active)
        item.branches = _filter_locations(item.branches, name, rel, active)
        if not item.branches:
            item.branch_values.clear()
    _remove_empty_keys(report)


def apply_lexical_hardening(root: Path, settings: Settings, report: ScanReport) -> None:
    """Remove regex detections whose API token occurs only in comments/non-executable text.

    The pass is conservative: it filters only locations emitted by built-in pattern adapters.
    AST-derived Python evidence, structured configuration declarations, validators, plugin
    evidence, runtime traces, and unrelated location details are left unchanged.
    """
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if settings.ignored(rel):
            continue
        suffix = path.suffix.lower()
        if suffix not in _RELEVANT_EXTENSIONS:
            continue
        try:
            if path.stat().st_size > settings.max_file_size:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        _filter_file(report, rel, text, suffix)
