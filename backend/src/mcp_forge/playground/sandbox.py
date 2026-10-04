"""Process-isolated playground subprocess launcher with scrubbed environment and process group management.

Note: Provides process-level isolation, isolated temporary scratchpaths, and environment
scrubbing. This is not hardware/container-level OS virtualization.
"""

import os
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path


class SandboxLauncher:
    """Manages the process-isolated execution environment and subprocess lifecycle of an MCP server."""

    def __init__(
        self,
        server_dir: Path,
        user_env_vars: dict[str, str] | None = None,
        base_url_override: str | None = None,
    ) -> None:
        self.server_dir = server_dir
        self.user_env_vars = user_env_vars or {}
        self.base_url_override = base_url_override
        self.temp_dir: Path | None = None
        self.process: subprocess.Popen[str] | None = None

    def build_scrubbed_env(self) -> dict[str, str]:
        """Construct a minimal scrubbed environment containing only required safe vars and user credentials."""
        # 1. Inherit only critical OS/runtime system variables
        safe_keys = {
            "PATH",
            "SYSTEMROOT",
            "WINDIR",
            "PYTHONPATH",
            "VIRTUAL_ENV",
            "LANG",
            "LC_ALL",
            "TZ",
        }
        env: dict[str, str] = {}
        for k in safe_keys:
            if k in os.environ:
                env[k] = os.environ[k]

        # 2. Redirect HOME / USERPROFILE / TEMP to isolated temporary directory
        if self.temp_dir:
            env["HOME"] = str(self.temp_dir)
            env["USERPROFILE"] = str(self.temp_dir)
            env["TMP"] = str(self.temp_dir)
            env["TEMP"] = str(self.temp_dir)

        # 3. Add server base directory to PYTHONPATH
        curr_pythonpath = env.get("PYTHONPATH", "")
        server_path_str = str(self.server_dir.resolve())
        env["PYTHONPATH"] = (
            f"{server_path_str}{os.pathsep}{curr_pythonpath}"
            if curr_pythonpath
            else server_path_str
        )

        # 4. Mandatory runtime settings
        env["MCP_TRANSPORT"] = "stdio"
        if self.base_url_override:
            env["API_BASE_URL"] = self.base_url_override

        # 5. User-supplied credentials for this session (kept in memory/process env only)
        for k, v in self.user_env_vars.items():
            if k and v:
                env[k] = v

        return env

    def start(self) -> subprocess.Popen[str]:
        """Create temp workspace and spawn server process with process group isolation."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="mcp_forge_playground_"))
        env = self.build_scrubbed_env()

        server_py = self.server_dir / "server.py"
        if not server_py.exists():
            raise FileNotFoundError(f"server.py not found in {self.server_dir}")

        creationflags = 0
        preexec_fn = None
        if sys.platform == "win32":
            # Windows: CREATE_NEW_PROCESS_GROUP
            creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        else:
            # POSIX: setsid for process group detachment and best-effort resource limits
            def _posix_setup() -> None:
                if hasattr(os, "setsid"):
                    os.setsid()
                try:
                    import resource

                    # 1 GB virtual memory address space limit
                    max_mem = 1024 * 1024 * 1024
                    resource.setrlimit(resource.RLIMIT_AS, (max_mem, max_mem))
                except Exception:  # noqa: S110
                    pass

            preexec_fn = _posix_setup

        self.process = subprocess.Popen(  # noqa: S603
            [sys.executable, str(server_py)],
            cwd=str(self.server_dir),
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
            creationflags=creationflags,
            preexec_fn=preexec_fn,
        )
        return self.process

    def terminate(self) -> None:
        """Kill entire process group and cleanup scratch temp directory."""
        if self.process and self.process.poll() is None:
            try:
                if sys.platform == "win32":
                    # Send CTRL_BREAK_EVENT or force terminate
                    try:
                        ctrl_break = getattr(signal, "CTRL_BREAK_EVENT", None)
                        if ctrl_break is not None:
                            self.process.send_signal(ctrl_break)
                    except Exception:  # noqa: S110
                        pass
                    self.process.kill()
                else:
                    try:
                        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    except Exception:  # noqa: S110
                        self.process.kill()
                self.process.wait(timeout=2.0)
            except Exception:  # noqa: S110
                pass
            finally:
                self.process = None

        # Clean up temp directory
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            except Exception:  # noqa: S110
                pass
            self.temp_dir = None
