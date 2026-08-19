"""Local filesystem isolated sandbox implementation with git tracking."""

import os
import shutil
import uuid
import tempfile
from pathlib import Path
from typing import Dict, Optional

from bca.core.types import DiffStats
from bca.sandbox.base import BaseSandbox, ProcessResult
from bca.sandbox.process import run_command_safe


class LocalSandbox(BaseSandbox):
    """
    Sandboxed workspace located in a temporary directory (e.g., /tmp/bca/trials/<id>).
    Tracks changes via local Git repository checkpointing.
    """

    def __init__(
        self,
        trial_id: Optional[str] = None,
        base_dir: Optional[Path] = None,
        preserve_on_exit: bool = False,
    ):
        self.trial_id = trial_id or str(uuid.uuid4())
        self.base_dir = base_dir or Path(tempfile.gettempdir()) / "bca" / "trials" / self.trial_id
        self._workspace = self.base_dir / "workspace"
        self.preserve_on_exit = preserve_on_exit
        self._initialized = False

    @property
    def workspace_path(self) -> Path:
        return self._workspace

    def setup(self, starter_dir: Optional[Path] = None) -> None:
        """Create workspace, copy starter files, and initialize git tracking."""
        if self._workspace.exists():
            shutil.rmtree(self._workspace, ignore_errors=True)

        self._workspace.mkdir(parents=True, exist_ok=True)

        if starter_dir and starter_dir.exists():
            # Copy all files from starter_dir into workspace
            for item in starter_dir.iterdir():
                dest = self._workspace / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)

        # Initialize local git repository for diff tracking
        run_command_safe("git init", cwd=self._workspace)
        run_command_safe("git config user.name 'BCA Bot'", cwd=self._workspace)
        run_command_safe("git config user.email 'bca-bot@local'", cwd=self._workspace)
        run_command_safe("git add -A", cwd=self._workspace)
        run_command_safe("git commit -m 'initial-state' --allow-empty", cwd=self._workspace)

        self._initialized = True

    def exec(
        self,
        cmd: str,
        timeout_seconds: Optional[int] = 120,
        extra_env: Optional[Dict[str, str]] = None,
        relative_cwd: Optional[str] = None,
    ) -> ProcessResult:
        if not self._initialized:
            self.setup()

        target_cwd = self._workspace
        if relative_cwd:
            target_cwd = (self._workspace / relative_cwd).resolve()

        return run_command_safe(
            cmd=cmd,
            cwd=target_cwd,
            timeout_seconds=timeout_seconds or 120,
            env=extra_env,
        )

    def read_file(self, relative_path: str) -> str:
        target = (self._workspace / relative_path).resolve()
        # Prevent path traversal outside sandbox
        if not str(target).startswith(str(self._workspace.resolve())):
            raise ValueError(f"Path traversal detected: {relative_path}")

        if not target.is_file():
            raise FileNotFoundError(f"File not found in sandbox: {relative_path}")

        return target.read_text(encoding="utf-8")

    def write_file(self, relative_path: str, content: str) -> None:
        target = (self._workspace / relative_path).resolve()
        if not str(target).startswith(str(self._workspace.resolve())):
            raise ValueError(f"Path traversal detected: {relative_path}")

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def get_diff(self) -> DiffStats:
        """Calculates git diff compared to initial checkpoint."""
        if not self._initialized or not (self._workspace / ".git").exists():
            return DiffStats()

        # Add all untracked files before diffing
        run_command_safe("git add -N .", cwd=self._workspace)
        diff_res = run_command_safe("git diff HEAD", cwd=self._workspace)
        numstat_res = run_command_safe("git diff --numstat HEAD", cwd=self._workspace)

        files_changed = 0
        insertions = 0
        deletions = 0

        for line in numstat_res.stdout.strip().splitlines():
            parts = line.split()
            if len(parts) >= 3:
                files_changed += 1
                try:
                    insertions += int(parts[0]) if parts[0] != "-" else 0
                    deletions += int(parts[1]) if parts[1] != "-" else 0
                except ValueError:
                    pass

        return DiffStats(
            files_changed=files_changed,
            insertions=insertions,
            deletions=deletions,
            patch=diff_res.stdout,
        )

    def cleanup(self) -> None:
        """Removes temporary sandbox directory."""
        if not self.preserve_on_exit and self.base_dir.exists():
            shutil.rmtree(self.base_dir, ignore_errors=True)
