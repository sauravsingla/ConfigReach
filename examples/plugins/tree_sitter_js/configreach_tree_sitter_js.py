from __future__ import annotations

import re
from pathlib import Path

import tree_sitter_javascript as tsjs
from tree_sitter import Language, Parser

from configreach.models import ConfigKey, Location


class TreeSitterJavaScriptAdapter:
    """Optional parser-backed example adapter kept outside the minimal core."""

    name = "tree-sitter-js"
    api_version = 1
    parser = "tree-sitter-javascript"
    deterministic = True
    capabilities = ("env-read", "line-provenance", "syntax-tree")

    _env = re.compile(r"process\.env\.([A-Z][A-Z0-9_]*)")

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in {".js", ".jsx", ".mjs", ".cjs"}

    def scan(self, *, path: Path, rel: str, text: str, is_test: bool, keys: dict[str, ConfigKey]) -> None:
        language = Language(tsjs.language())
        parser = Parser(language)
        source = text.encode("utf-8")
        tree = parser.parse(source)
        stack = [tree.root_node]
        while stack:
            node = stack.pop()
            stack.extend(reversed(node.children))
            if node.type != "member_expression":
                continue
            snippet = source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")
            match = self._env.fullmatch(snippet)
            if not match:
                continue
            name = match.group(1)
            key = keys.setdefault(name, ConfigKey(name=name))
            key.languages.add("javascript")
            key.categories.add("env")
            location = Location(
                rel,
                node.start_point.row + 1,
                "test" if is_test else "read",
                "plugin:tree-sitter-js",
            )
            (key.test_mentions if is_test else key.reads).append(location)
