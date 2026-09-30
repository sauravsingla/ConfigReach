from __future__ import annotations

import re
from pathlib import Path

import tree_sitter_go as tsgo
from tree_sitter import Language, Parser

from configreach.models import ConfigKey, Location


class TreeSitterGoAdapter:
    """Optional parser-backed Go example for Adapter API v1."""

    name = "tree-sitter-go"
    api_version = 1
    parser = "tree-sitter-go"
    deterministic = True
    capabilities = ("env-read", "line-provenance", "syntax-tree")

    _env = re.compile(r'os\.(?:Getenv|LookupEnv)\("([A-Z][A-Z0-9_]*)"\)')

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() == ".go"

    def scan(self, *, path: Path, rel: str, text: str, is_test: bool, keys: dict[str, ConfigKey]) -> None:
        language = Language(tsgo.language())
        parser = Parser(language)
        source = text.encode("utf-8")
        tree = parser.parse(source)
        stack = [tree.root_node]
        while stack:
            node = stack.pop()
            stack.extend(reversed(node.children))
            if node.type != "call_expression":
                continue
            snippet = source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")
            match = self._env.fullmatch(snippet)
            if not match:
                continue
            name = match.group(1)
            key = keys.setdefault(name, ConfigKey(name=name))
            key.languages.add("go")
            key.categories.add("env")
            location = Location(
                rel,
                node.start_point.row + 1,
                "test" if is_test else "read",
                "plugin:tree-sitter-go",
            )
            (key.test_mentions if is_test else key.reads).append(location)
