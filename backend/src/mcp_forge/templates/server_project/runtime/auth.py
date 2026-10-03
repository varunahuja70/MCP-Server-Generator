"""Runtime authentication handlers: API key, bearer, basic, and OAuth2 client credentials."""

import base64
import os
import time
from typing import Any

import httpx


class OAuth2TokenCache:
    """In-memory cache for OAuth2 client-credentials tokens."""

    def __init__(self) -> None:
        self.access_token: str | None = None
        self.expires_at: float = 0.0

    def is_valid(self) -> bool:
        # 30-second safety margin
        return bool(self.access_token and time.time() < (self.expires_at - 30))

    def set_token(self, token: str, expires_in: int) -> None:
        self.access_token = token
        self.expires_at = time.time() + expires_in


_OAUTH2_CACHE = OAuth2TokenCache()


async def get_oauth2_token(
    client_id: str,
    client_secret: str,
    token_url: str,
    client: httpx.AsyncClient | None = None,
) -> str:
    """Fetch or return cached OAuth2 client credentials access token."""
    if _OAUTH2_CACHE.is_valid() and _OAUTH2_CACHE.access_token:
        return _OAUTH2_CACHE.access_token

    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }

    should_close = False
    if client is None:
        client = httpx.AsyncClient(timeout=15.0)
        should_close = True

    try:
        resp = await client.post(token_url, data=payload)
        resp.raise_for_status()
        data = resp.json()
        token: str = str(data.get("access_token", ""))
        expires_in = int(data.get("expires_in", 3600))
        _OAUTH2_CACHE.set_token(token, expires_in)
        return token
    finally:
        if should_close:
            await client.aclose()


async def apply_auth(
    security_requirements: list[dict[str, list[str]]],
    auth_definitions: dict[str, Any],
    headers: dict[str, str],
    query_params: dict[str, Any],
    cookies: dict[str, str],
    client: httpx.AsyncClient | None = None,
) -> None:
    """Apply authentication credentials to headers, query params, or cookies based on operation security."""
    if not security_requirements:
        return

    # Try each security option (OR logic between items in the list)
    for req in security_requirements:
        # Check if all schemes in this requirement are fulfilled
        all_satisfied = True
        temp_headers: dict[str, str] = {}
        temp_query: dict[str, Any] = {}
        temp_cookies: dict[str, str] = {}

        for scheme_name in req:
            scheme_info = auth_definitions.get(scheme_name, {})
            env_map = scheme_info.get("env_mapping", {})
            stype = scheme_info.get("type")
            in_loc = scheme_info.get("in")
            param_name = scheme_info.get("param_name") or "X-API-Key"

            if stype == "apiKey":
                var_name = env_map.get("api_key")
                val = os.environ.get(var_name, "") if var_name else ""
                if not val:
                    all_satisfied = False
                    break
                if in_loc == "header":
                    temp_headers[param_name] = val
                elif in_loc == "query":
                    temp_query[param_name] = val
                elif in_loc == "cookie":
                    temp_cookies[param_name] = val

            elif stype == "http":
                scheme = (scheme_info.get("scheme") or "").lower()
                if scheme == "bearer":
                    var_name = env_map.get("bearer_token")
                    token = os.environ.get(var_name, "") if var_name else ""
                    if not token:
                        all_satisfied = False
                        break
                    temp_headers["Authorization"] = f"Bearer {token}"
                elif scheme == "basic":
                    u_var = env_map.get("username")
                    p_var = env_map.get("password")
                    user = os.environ.get(u_var, "") if u_var else ""
                    password = os.environ.get(p_var, "") if p_var else ""
                    if not user:
                        all_satisfied = False
                        break
                    b64 = base64.b64encode(f"{user}:{password}".encode()).decode()
                    temp_headers["Authorization"] = f"Basic {b64}"

            elif stype == "oauth2":
                id_var = env_map.get("client_id")
                secret_var = env_map.get("client_secret")
                url_var = env_map.get("token_url")
                cid = os.environ.get(id_var, "") if id_var else ""
                csecret = os.environ.get(secret_var, "") if secret_var else ""
                turl = os.environ.get(url_var, "") if url_var else ""
                if not cid or not csecret or not turl:
                    all_satisfied = False
                    break
                token = await get_oauth2_token(cid, csecret, turl, client=client)
                temp_headers["Authorization"] = f"Bearer {token}"

        if all_satisfied:
            headers.update(temp_headers)
            query_params.update(temp_query)
            cookies.update(temp_cookies)
            return
