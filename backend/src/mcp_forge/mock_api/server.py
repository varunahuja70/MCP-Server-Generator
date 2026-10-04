"""In-process mock HTTP server on a random loopback port for Playground sessions."""

import asyncio
import json
from typing import Any

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from mcp_forge.core.ir.models import IRApi
from mcp_forge.mock_api.builder import MockApiBuilder


class MockServer:
    """An in-process HTTP mock server backed by Starlette and Uvicorn."""

    def __init__(self, ir: IRApi, host: str = "127.0.0.1", port: int = 0) -> None:
        self.ir = ir
        self.host = host
        self.port = port
        self.builder = MockApiBuilder(ir)
        self.server: uvicorn.Server | None = None
        self._task: asyncio.Task[None] | None = None
        self.base_url: str = ""

    def create_app(self) -> Starlette:
        """Create Starlette application that routes all requests through MockApiBuilder."""
        app = Starlette()

        async def catch_all(request: Request) -> Response:
            method = request.method
            path = request.url.path
            query_params = dict(request.query_params)
            headers = dict(request.headers)

            body: Any = None
            if method in ("POST", "PUT", "PATCH"):
                body_bytes = await request.body()
                if body_bytes:
                    try:
                        body = json.loads(body_bytes.decode("utf-8"))
                    except Exception:
                        body = body_bytes.decode("utf-8", errors="replace")

            status_code, resp_headers, resp_data = self.builder.handle_request(
                method=method,
                path=path,
                query_params=query_params,
                headers=headers,
                body=body,
            )

            if status_code == 204 or resp_data is None:
                return Response(status_code=204, headers=resp_headers)

            if isinstance(resp_data, (dict, list)):
                return JSONResponse(resp_data, status_code=status_code, headers=resp_headers)

            return Response(
                content=str(resp_data),
                status_code=status_code,
                headers=resp_headers,
            )

        app.add_route(
            "/{path:path}",
            catch_all,
            methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
        )
        return app

    async def start(self) -> str:
        """Start the in-process mock server on loopback and return base_url."""
        app = self.create_app()
        config = uvicorn.Config(
            app=app,
            host=self.host,
            port=self.port,
            log_level="error",
        )
        self.server = uvicorn.Server(config)

        # Start server in background task
        self._task = asyncio.create_task(self.server.serve())

        # Wait until server has started and bound port
        while not self.server.started:
            await asyncio.sleep(0.02)

        # Extract actual bound port
        for server in self.server.servers:
            for sock in server.sockets:
                self.port = sock.getsockname()[1]
                break
            if self.port != 0:
                break

        self.base_url = f"http://{self.host}:{self.port}"
        return self.base_url

    async def stop(self) -> None:
        """Stop the in-process mock server."""
        if self.server:
            self.server.should_exit = True
        if self._task:
            await self._task
            self._task = None
