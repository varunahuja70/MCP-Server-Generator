"""Defensive YAML parser with alias expansion and nesting depth limits."""

from typing import Any

import yaml
from yaml.composer import Composer
from yaml.constructor import SafeConstructor
from yaml.parser import Parser
from yaml.reader import Reader
from yaml.resolver import Resolver
from yaml.scanner import Scanner

from mcp_forge.errors import InvalidSpecError

DEFAULT_MAX_ALIASES = 50
DEFAULT_MAX_DEPTH = 30


class GuardedSafeLoader(Reader, Scanner, Parser, Composer, SafeConstructor, Resolver):
    """Safe YAML loader that limits alias count and recursion depth."""

    def __init__(
        self,
        stream: Any,
        max_aliases: int = DEFAULT_MAX_ALIASES,
        max_depth: int = DEFAULT_MAX_DEPTH,
    ) -> None:
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        SafeConstructor.__init__(self)
        Resolver.__init__(self)
        self.max_aliases = max_aliases
        self.max_depth = max_depth
        self.alias_count = 0
        self.current_depth = 0

    def compose_node(self, parent: Any, index: Any) -> Any:
        if self.check_event(yaml.AliasEvent):
            self.alias_count += 1
            if self.alias_count > self.max_aliases:
                raise InvalidSpecError(
                    f"YAML alias count exceeded safety limit of {self.max_aliases}. "
                    "Possible billion-laughs DoS attack detected.",
                    details={"max_aliases": self.max_aliases},
                )

        self.current_depth += 1
        if self.current_depth > self.max_depth:
            raise InvalidSpecError(
                f"YAML nesting depth exceeded safety limit of {self.max_depth}.",
                details={"max_depth": self.max_depth},
            )

        try:
            return super().compose_node(parent, index)
        finally:
            self.current_depth -= 1


def safe_load_yaml(
    content: str,
    max_aliases: int = DEFAULT_MAX_ALIASES,
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> Any:
    """Parse YAML string safely with strict limits on aliases and recursion depth."""
    if not content or not content.strip():
        return {}

    try:
        loader = GuardedSafeLoader(
            content,
            max_aliases=max_aliases,
            max_depth=max_depth,
        )
        try:
            return loader.get_single_data()
        finally:
            loader.dispose()
    except yaml.YAMLError as e:
        raise InvalidSpecError(f"YAML parsing error: {e}") from e
