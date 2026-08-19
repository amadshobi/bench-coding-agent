"""Docker-based container sandbox isolation."""

import shutil
import uuid
from pathlib import Path
from typing import Dict, Optional

from bca.core.types import DiffStats
from bca.sandbox.base import BaseSandbox, ProcessResult
from bca.sandbox.local import LocalSandbox
from bca.sandbox.process import run_command_safe


class DockerSandbox(BaseSandbox):
    """
    Docker container sandbox. Falls back gracefully to LocalSandbox if docker is not installed.
    """

    def __init__(
        self,
        trial_id: Optional[str] = None,
        image: str = "python:3.14-slim",
        preserve_on_exit: bool = False,
    ):
        self.trial_id = trial_id or str(uuid.uuid4())
        self.image = image
        self.preserve_on_exit = preserve_on_exit
        self.container_name = f"bca-trial-{self.trial_id[:8]}"
        self._local_fallback = LocalSandbox(
            trial_id=self.trial_id,
            preserve_on_exit=preserve_on_exit,
        )
        self.docker_available = shutil.which("docker") is not None
        self._container_running = False

    @property
    def workspace_path(self) -> Path:
        return self._local_fallback.workspace_path

    def setup(self, starter_dir: Optional[Path] = None) -> None:
        self._local_fallback.setup(starter_dir)
        if not self.docker_available:
            return

        # Try to run background docker container mounting the local workspace
        ws_abs = str(self._local_fallback.workspace_path.resolve())
        cmd = f"docker run -d --name {self.container_name} -v {ws_abs}:/workspace -w /workspace {self.image} tail -f /dev/null"
        res = run_command_safe(cmd, cwd=self._local_fallback.workspace_path, timeout_seconds=60)
        if res.exit_code == 0:
            self._container_running = True

    def exec(
        self,
        cmd: str,
        timeout_seconds: Optional[int] = 120,
        extra_env: Optional[Dict[str, str]] = None,
        relative_cwd: Optional[str] = None,
    ) -> ProcessResult:
        if not self._container_running:
            return self._local_fallback.exec(cmd, timeout_seconds, extra_env, relative_cwd)

        env_flags = ""
        if extra_env:
            for k, v in extra_env.items():
                env_flags += f" -e {k}='{v}'"

        workdir = "/workspace"
        if relative_cwd:
            workdir = f"/workspace/{relative_cwd}"

        docker_cmd = f"docker exec {env_flags} -w {workdir} {self.container_name} bash -c '{cmd}'"
        return run_command_safe(
            docker_cmd,
            cwd=self._local_fallback.workspace_path,
            timeout_seconds=timeout_seconds or 120,
        )

    def read_file(self, relative_path: str) -> str:
        return self._local_fallback.read_file(relative_path)

    def write_file(self, relative_path: str, content: str) -> None:
        self._local_fallback.write_file(relative_path, content)

    def get_diff(self) -> DiffStats:
        return self._local_fallback.get_diff()

    def cleanup(self) -> None:
        if self._container_running:
            run_command_safe(f"docker rm -f {self.container_name}", cwd=Path("/tmp"))
            self._container_running = False
        self._local_fallback.cleanup()
