"""Sandbox layer exports and factory helper."""

from typing import Optional
from pathlib import Path

from bca.core.types import SandboxMode
from bca.sandbox.base import BaseSandbox, ProcessResult
from bca.sandbox.local import LocalSandbox
from bca.sandbox.docker import DockerSandbox
from bca.sandbox.shadow import ShadowCloneSandbox
from bca.sandbox.process import run_command_safe


def create_sandbox(
    mode: str = "shadow",
    trial_id: Optional[str] = None,
    preserve_on_exit: bool = False,
) -> BaseSandbox:
    """Factory to instantiate the appropriate sandbox environment. Defaults to shadow clone."""
    if mode == SandboxMode.DOCKER.value or mode == "docker":
        return DockerSandbox(trial_id=trial_id, preserve_on_exit=preserve_on_exit)
    elif mode == SandboxMode.LOCAL.value or mode == "local":
        return LocalSandbox(trial_id=trial_id, preserve_on_exit=preserve_on_exit)
    # Default to ShadowCloneSandbox (CoW read-only host mirror + isolated workspace)
    return ShadowCloneSandbox(trial_id=trial_id, preserve_on_exit=preserve_on_exit)


__all__ = [
    "BaseSandbox",
    "ProcessResult",
    "LocalSandbox",
    "DockerSandbox",
    "ShadowCloneSandbox",
    "create_sandbox",
    "run_command_safe",
]
