"""MCP client adapter using official SDK ClientSession communicating over stdio with trace capture."""

import asyncio
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from mcp_forge.playground.sandbox import SandboxLauncher
from mcp_forge.playground.trace import TraceRecorder


class PlaygroundClient:
    """Client for communicating with the sandboxed MCP server over stdio with full trace capture.

    Runs stdio_client and ClientSession inside a dedicated background task to ensure
    anyio task groups / cancel scopes are always created and destroyed on the same task.
    """

    def __init__(self, sandbox: SandboxLauncher, trace: TraceRecorder) -> None:
        self.sandbox = sandbox
        self.trace = trace
        self._loop_task: asyncio.Task[None] | None = None
        self._cmd_queue: asyncio.Queue[tuple[str, dict[str, Any], asyncio.Future[Any]] | None] = (
            asyncio.Queue()
        )
        self._connected = False

    async def connect(self) -> dict[str, Any]:
        """Establish stdio connection with the MCP server subprocess and perform handshake."""
        # Setup temp workspace
        if not self.sandbox.temp_dir:
            self.sandbox.temp_dir = Path(tempfile.mkdtemp(prefix="mcp_forge_playground_"))

        init_future: asyncio.Future[dict[str, Any]] = asyncio.get_running_loop().create_future()
        self._loop_task = asyncio.create_task(self._worker_loop(init_future))

        # Await worker connection and initialization
        res = await init_future
        self._connected = True
        return res

    async def _worker_loop(self, init_future: asyncio.Future[dict[str, Any]]) -> None:
        """Dedicated worker task managing stdio_client and ClientSession lifecycle."""
        env = self.sandbox.build_scrubbed_env()
        server_py = self.sandbox.server_dir / "server.py"

        server_params = StdioServerParameters(
            command=sys.executable,
            args=[str(server_py)],
            env=env,
            cwd=str(self.sandbox.server_dir),
        )

        try:
            start_time = time.time()
            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    # Record initialize
                    self.trace.record(
                        "client_to_server", {"jsonrpc": "2.0", "method": "initialize"}
                    )
                    init_res = await session.initialize()
                    duration_ms = (time.time() - start_time) * 1000

                    res_dict = {
                        "protocolVersion": init_res.protocol_version,
                        "serverInfo": {
                            "name": init_res.server_info.name,
                            "version": init_res.server_info.version,
                        },
                        "capabilities": init_res.capabilities.model_dump(),
                    }
                    self.trace.record("server_to_client", res_dict, duration_ms=duration_ms)

                    if not init_future.done():
                        init_future.set_result(res_dict)

                    # Command processing loop
                    while True:
                        cmd = await self._cmd_queue.get()
                        if cmd is None:
                            # Shutdown signal
                            break

                        action, args, future = cmd
                        if future.done():
                            continue

                        try:
                            if action == "list_tools":
                                t_start = time.time()
                                self.trace.record(
                                    "client_to_server", {"jsonrpc": "2.0", "method": "tools/list"}
                                )
                                tools_res = await session.list_tools()
                                t_dur = (time.time() - t_start) * 1000
                                tool_list = [
                                    {
                                        "name": t.name,
                                        "description": t.description,
                                        "input_schema": t.input_schema,
                                        "annotations": t.annotations.model_dump()
                                        if t.annotations
                                        else {},
                                    }
                                    for t in tools_res.tools
                                ]
                                self.trace.record(
                                    "server_to_client", {"tools": tool_list}, duration_ms=t_dur
                                )
                                future.set_result(tool_list)

                            elif action == "call_tool":
                                t_name = args["name"]
                                t_args = args["arguments"]
                                timeout_s = args.get("timeout_s", 30.0)

                                req_payload = {
                                    "jsonrpc": "2.0",
                                    "method": "tools/call",
                                    "params": {"name": t_name, "arguments": t_args},
                                }
                                t_start = time.time()
                                self.trace.record("client_to_server", req_payload)

                                try:
                                    call_res = await asyncio.wait_for(
                                        session.call_tool(t_name, t_args),
                                        timeout=timeout_s,
                                    )
                                    t_dur = (time.time() - t_start) * 1000
                                    content_list = []
                                    for item in call_res.content:
                                        if hasattr(item, "text"):
                                            content_list.append({"type": "text", "text": item.text})
                                        else:
                                            content_list.append(
                                                {"type": "other", "data": str(item)}
                                            )

                                    resp_payload = {
                                        "content": content_list,
                                        "isError": getattr(call_res, "is_error", False),
                                    }
                                    self.trace.record(
                                        "server_to_client", resp_payload, duration_ms=t_dur
                                    )
                                    future.set_result(resp_payload)

                                except TimeoutError:
                                    t_dur = (time.time() - t_start) * 1000
                                    err_payload = {
                                        "error": f"Tool call timed out after {timeout_s}s",
                                        "isError": True,
                                    }
                                    self.trace.record(
                                        "server_to_client", err_payload, duration_ms=t_dur
                                    )
                                    future.set_result(err_payload)
                                except Exception as e:
                                    t_dur = (time.time() - t_start) * 1000
                                    err_payload = {"error": str(e), "isError": True}
                                    self.trace.record(
                                        "server_to_client", err_payload, duration_ms=t_dur
                                    )
                                    future.set_result(err_payload)
                            else:
                                future.set_exception(ValueError(f"Unknown action: {action}"))
                        except Exception as e:
                            if not future.done():
                                future.set_exception(e)
        except Exception as e:
            if not init_future.done():
                init_future.set_exception(e)
        finally:
            self._connected = False

    async def list_tools(self) -> list[dict[str, Any]]:
        """Query server for list of available tools."""
        if not self._connected or not self._loop_task or self._loop_task.done():
            raise RuntimeError("Playground client is not connected.")

        future: asyncio.Future[list[dict[str, Any]]] = asyncio.get_running_loop().create_future()
        await self._cmd_queue.put(("list_tools", {}, future))
        return await future

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        timeout_s: float = 30.0,
    ) -> dict[str, Any]:
        """Dispatch tool invocation with argument scrubbing, timeout, and trace capture."""
        if not self._connected or not self._loop_task or self._loop_task.done():
            raise RuntimeError("Playground client is not connected.")

        future: asyncio.Future[dict[str, Any]] = asyncio.get_running_loop().create_future()
        await self._cmd_queue.put(
            (
                "call_tool",
                {"name": name, "arguments": arguments, "timeout_s": timeout_s},
                future,
            )
        )
        return await future

    async def disconnect(self) -> None:
        """Close client session and stdio transports cleanly."""
        if self._loop_task and not self._loop_task.done():
            await self._cmd_queue.put(None)
            try:
                await asyncio.wait_for(self._loop_task, timeout=5.0)
            except (TimeoutError, asyncio.CancelledError):
                self._loop_task.cancel()
        self._connected = False
