"""JSON Pointer $ref resolution with cycle detection and depth protection."""

from typing import Any

from mcp_forge.errors import InvalidSpecError


def _unescape_pointer_token(token: str) -> str:
    """Unescape RFC 6901 JSON Pointer token (~1 -> /, ~0 -> ~)."""
    return token.replace("~1", "/").replace("~0", "~")


def lookup_local_ref(root: dict[str, Any], ref: str) -> Any:
    """Resolve a local JSON Pointer reference (#/path/to/token) against root document."""
    if not ref.startswith("#"):
        raise InvalidSpecError(f"Expected local $ref starting with '#', got '{ref}'.")

    path_part = ref.lstrip("#").lstrip("/")
    if not path_part:
        return root

    tokens = [_unescape_pointer_token(t) for t in path_part.split("/")]
    current: Any = root

    for token in tokens:
        if isinstance(current, dict):
            if token in current:
                current = current[token]
            else:
                raise InvalidSpecError(
                    f"Unable to resolve $ref '{ref}': key '{token}' not found.",
                    details={"ref": ref, "missing_token": token},
                )
        elif isinstance(current, list):
            try:
                idx = int(token)
                current = current[idx]
            except (ValueError, IndexError) as e:
                raise InvalidSpecError(
                    f"Unable to resolve $ref '{ref}': index '{token}' invalid.",
                    details={"ref": ref, "index": token},
                ) from e
        else:
            raise InvalidSpecError(
                f"Unable to resolve $ref '{ref}': encountered non-container at '{token}'.",
                details={"ref": ref},
            )

    return current


def resolve_refs(
    node: Any,
    root: dict[str, Any],
    allow_remote: bool = False,
    seen_refs: set[str] | None = None,
    current_depth: int = 0,
    max_depth: int = 15,
) -> Any:
    """Recursively resolve $ref references while cutting circular dependencies and depth limits."""
    if current_depth > max_depth:
        return {
            "type": "object",
            "description": "Schema simplified: exceeded maximum resolution depth.",
            "x-cut-depth": True,
        }

    visited = set(seen_refs or set())

    if isinstance(node, dict):
        if "$ref" in node and isinstance(node["$ref"], str):
            ref = node["$ref"]
            if not ref.startswith("#"):
                if not allow_remote:
                    raise InvalidSpecError(
                        f"Remote $ref resolution is disabled by security policy: '{ref}'.",
                        details={"ref": ref},
                    )
                # If remote refs are not implemented in V1, reject
                raise InvalidSpecError(
                    f"Remote reference '{ref}' is not supported in V1.",
                    details={"ref": ref},
                )

            # Cycle detection
            if ref in visited:
                return {
                    "type": "object",
                    "description": f"Circular reference to {ref}.",
                    "x-circular-ref": ref,
                }

            visited.add(ref)
            target = lookup_local_ref(root, ref)

            # Preserve sibling properties (like description overrides in OAS 3.1)
            resolved_target = resolve_refs(
                target,
                root=root,
                allow_remote=allow_remote,
                seen_refs=visited,
                current_depth=current_depth + 1,
                max_depth=max_depth,
            )

            if isinstance(resolved_target, dict):
                merged = dict(resolved_target)
                for k, v in node.items():
                    if k != "$ref":
                        merged[k] = resolve_refs(
                            v,
                            root=root,
                            allow_remote=allow_remote,
                            seen_refs=visited,
                            current_depth=current_depth + 1,
                            max_depth=max_depth,
                        )
                return merged

            return resolved_target

        # Normal dictionary: resolve all entries
        return {
            k: resolve_refs(
                v,
                root=root,
                allow_remote=allow_remote,
                seen_refs=visited,
                current_depth=current_depth,
                max_depth=max_depth,
            )
            for k, v in node.items()
        }

    elif isinstance(node, list):
        return [
            resolve_refs(
                item,
                root=root,
                allow_remote=allow_remote,
                seen_refs=visited,
                current_depth=current_depth,
                max_depth=max_depth,
            )
            for item in node
        ]

    return node
