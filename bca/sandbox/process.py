"""Safe subprocess execution with process group termination and timeouts."""

import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Dict, Optional

from bca.sandbox.base import ProcessResult


def run_command_safe(
    cmd: str,
    cwd: Path,
    timeout_seconds: int = 120,
    env: Optional[Dict[str, str]] = None,
    shell: bool = True,
) -> ProcessResult:
    """
    Executes a command safely inside `cwd` with a strict timeout.
    Uses process groups (os.setsid) to ensure all child processes are killed on timeout.
    """
    start_time = time.perf_counter()
    full_env = dict(os.environ)
    if env:
        full_env.update(env)

    # Disable interactive prompts
    full_env["DEBIAN_FRONTEND"] = "noninteractive"
    full_env["CI"] = "1"
    full_env["PYTHONUNBUFFERED"] = "1"

    proc = None
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            env=full_env,
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid,  # Create new process group
        )

        stdout, stderr = proc.communicate(timeout=timeout_seconds)
        duration = time.perf_counter() - start_time
        return ProcessResult(
            command=cmd,
            exit_code=proc.returncode,
            stdout=stdout or "",
            stderr=stderr or "",
            duration_seconds=round(duration, 3),
            timed_out=False,
        )

    except subprocess.TimeoutExpired:
        if proc:
            try:
                # Kill the whole process group
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            stdout, stderr = proc.communicate()
        else:
            stdout, stderr = "", ""

        duration = time.perf_counter() - start_time
        return ProcessResult(
            command=cmd,
            exit_code=124,  # Standard timeout exit code
            stdout=stdout or "",
            stderr=(stderr or "") + f"\n[BCA] Command timed out after {timeout_seconds} seconds.",
            duration_seconds=round(duration, 3),
            timed_out=True,
        )

    except Exception as exc:
        duration = time.perf_counter() - start_time
        return ProcessResult(
            command=cmd,
            exit_code=1,
            stdout="",
            stderr=f"[BCA] Process execution error: {str(exc)}",
            duration_seconds=round(duration, 3),
            timed_out=False,
        )
