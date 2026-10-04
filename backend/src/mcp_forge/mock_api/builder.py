"""Route building and request dispatching for mock API."""

import re
from typing import Any

from mcp_forge.core.ir.models import IRApi, IROperation
from mcp_forge.mock_api.data_gen import MockDataGenerator

PATH_PARAM_REGEX = re.compile(r"\{([a-zA-Z0-9_]+)\}")


class MockRoute:
    """A matched mock route for an operation."""

    def __init__(self, op: IROperation) -> None:
        self.operation = op
        self.method = op.method.upper()
        self.path_template = op.path

        # Convert /pet/{petId} to regex ^/pet/(?P<petId>[^/]+)$
        pattern_str = "^" + PATH_PARAM_REGEX.sub(r"(?P<\1>[^/]+)", op.path) + "$"
        self.regex = re.compile(pattern_str)

    def matches(self, method: str, path: str) -> tuple[bool, dict[str, str]]:
        """Check if HTTP method and path match this route, returning extracted path params."""
        if self.method != method.upper():
            return False, {}

        match = self.regex.match(path)
        if not match:
            return False, {}

        return True, match.groupdict()


class MockApiBuilder:
    """Build mock router from an IRApi definition."""

    def __init__(self, ir: IRApi, data_gen: MockDataGenerator | None = None) -> None:
        self.ir = ir
        self.data_gen = data_gen or MockDataGenerator()
        self.routes: list[MockRoute] = [MockRoute(op) for op in ir.operations]

    def find_route(self, method: str, path: str) -> tuple[MockRoute | None, dict[str, str]]:
        """Find matching route for method and path."""
        for route in self.routes:
            matched, path_params = route.matches(method, path)
            if matched:
                return route, path_params
        return None, {}

    def handle_request(
        self,
        method: str,
        path: str,
        query_params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        body: Any = None,
        mock_status_override: int | None = None,
    ) -> tuple[int, dict[str, str], Any]:
        """Dispatch request to route and generate realistic mock response.

        Returns (status_code, response_headers, response_body).
        """
        headers = headers or {}
        # 1. Check X-Mock-Status header override for error simulation
        if mock_status_override:
            status = mock_status_override
        elif "x-mock-status" in {k.lower(): v for k, v in headers.items()}:
            for k, v in headers.items():
                if k.lower() == "x-mock-status":
                    try:
                        status = int(v)
                        break
                    except ValueError:
                        pass
        else:
            status = None

        route, _ = self.find_route(method, path)
        if not route:
            return 404, {"content-type": "application/json"}, {"error": "Not Found", "path": path}

        op = route.operation

        # If status override was requested, find matching response schema or return generic error
        if status is not None:
            resp_spec = op.responses.get(str(status))
            if resp_spec and resp_spec.schema_dict:
                resp_data = self.data_gen.generate(resp_spec.schema_dict)
            else:
                resp_data = {"error": f"Simulated status {status}", "status": status}
            return status, {"content-type": "application/json"}, resp_data

        # 2. Pick primary successful response (200, 201, 204, 'default', or first available)
        chosen_status = 200
        chosen_resp = None

        for code in ["200", "201", "202", "204"]:
            if code in op.responses:
                chosen_status = int(code)
                chosen_resp = op.responses[code]
                break

        if not chosen_resp:
            for code, resp in op.responses.items():
                if code.isdigit() and code.startswith("2"):
                    chosen_status = int(code)
                    chosen_resp = resp
                    break

        if not chosen_resp and op.responses:
            first_code = list(op.responses.keys())[0]
            chosen_status = int(first_code) if first_code.isdigit() else 200
            chosen_resp = op.responses[first_code]

        if chosen_status == 204:
            return 204, {}, None

        resp_schema = chosen_resp.schema_dict if chosen_resp else None
        resp_data = self.data_gen.generate(resp_schema)

        content_type = (
            chosen_resp.content_type
            if chosen_resp and chosen_resp.content_type
            else "application/json"
        )
        return chosen_status, {"content-type": content_type}, resp_data
