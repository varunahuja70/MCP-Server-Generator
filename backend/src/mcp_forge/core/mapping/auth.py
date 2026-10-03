"""Map OpenAPI security schemes to environment variables."""

import re
from typing import Any

from mcp_forge.core.ir.models import IRSecurityScheme


def _to_env_var_name(text: str) -> str:
    """Convert scheme name to upper snake case environment variable name."""
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")
    return s.upper() or "AUTH"


def map_security_scheme_to_env(
    scheme: IRSecurityScheme,
) -> tuple[dict[str, str], list[str], str | None]:
    """Map an IRSecurityScheme to required environment variable names.

    Returns:
        (env_mapping, env_var_names, unsupported_reason)
    """
    prefix = _to_env_var_name(scheme.name)
    env_mapping: dict[str, str] = {}
    env_vars: list[str] = []
    unsupported_reason: str | None = None

    if scheme.type == "apiKey":
        var_name = f"{prefix}_API_KEY"
        env_mapping["api_key"] = var_name
        env_vars.append(var_name)

    elif scheme.type == "http":
        if scheme.scheme and scheme.scheme.lower() == "bearer":
            var_name = f"{prefix}_BEARER_TOKEN"
            env_mapping["bearer_token"] = var_name
            env_vars.append(var_name)
        elif scheme.scheme and scheme.scheme.lower() == "basic":
            user_var = f"{prefix}_USERNAME"
            pass_var = f"{prefix}_PASSWORD"
            env_mapping["username"] = user_var
            env_mapping["password"] = pass_var
            env_vars.extend([user_var, pass_var])
        else:
            unsupported_reason = f"Unsupported HTTP auth scheme: '{scheme.scheme}'"

    elif scheme.type == "oauth2":
        flows = scheme.flows or {}
        flow_type = flows.get("flow")
        if flow_type in ("clientCredentials", "application") or "clientCredentials" in flows:
            id_var = f"{prefix}_CLIENT_ID"
            secret_var = f"{prefix}_CLIENT_SECRET"
            token_url_var = f"{prefix}_TOKEN_URL"
            env_mapping["client_id"] = id_var
            env_mapping["client_secret"] = secret_var
            env_mapping["token_url"] = token_url_var
            env_vars.extend([id_var, secret_var, token_url_var])
        else:
            unsupported_reason = f"OAuth2 flow '{flow_type}' is interactive and not supported for autonomous MCP server."

    else:
        unsupported_reason = f"Security scheme type '{scheme.type}' is not supported in V1."

    return env_mapping, env_vars, unsupported_reason


def map_all_security_schemes(
    schemes: dict[str, IRSecurityScheme],
) -> dict[str, Any]:
    """Build full authentication mapping dictionary for manifest."""
    result: dict[str, Any] = {}
    for name, scheme in schemes.items():
        mapping, env_vars, unsupported = map_security_scheme_to_env(scheme)
        result[name] = {
            "type": scheme.type,
            "scheme": scheme.scheme,
            "in": scheme.in_loc,
            "param_name": scheme.param_name,
            "env_mapping": mapping,
            "required_env_vars": env_vars,
            "supported": unsupported is None,
            "unsupported_reason": unsupported,
        }
    return result
