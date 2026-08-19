"""Abstract base class for execution sandboxes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

from bca.core.types import DiffStats


@dataclass(frozen=True)
class ProcessResult:
    """Result of executing a command in the sandbox."""
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False


class BaseSandbox(ABC):
    """Abstract contract for isolated sandbox environments."""

    @property
    @abstractmethod
    def workspace_path(self) -> Path:
        """Absolute path to the workspace root directory inside the sandbox."""
        ...

    @abstractmethod
    def setup(self, starter_dir: Optional[Path] = None) -> None:
        """Initialize the sandbox environment and copy starter code if provided."""
        ...

    @abstractmethod
    def exec(
        self,
        cmd: str,
        timeout_seconds: Optional[int] = None,
        extra_env: Optional[Dict[str, str]] = None,
        relative_cwd: Optional[str] = None,
    ) -> ProcessResult:
        """Execute a shell command inside the sandbox."""
        ...

    @abstractmethod
    def read_file(self, relative_path: str) -> str:
        """Read text content from a file within the sandbox workspace."""
        ...

    @abstractmethod
    def write_file(self, relative_path: str, content: str) -> None:
        """Write text content to a file within the sandbox workspace."""
        ...

    @abstractmethod
    def get_diff(self) -> DiffStats:
        """Extract git diff and modification statistics made in the workspace."""
        ...

    @abstractmethod
    def cleanup(self) -> None:
        """Tear down and clean up resources associated with this sandbox."""
        ...

    def __enter__(self) -> "BaseSandbox":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cleanup()
