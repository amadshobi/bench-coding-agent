"""Task specification and requirement schemas."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class TaskRequirement:
    """System and environment requirements for a task."""
    timeout_seconds: int = 180
    max_memory_mb: int = 1024
    network_access: bool = False
    python_version: str = "3.14"
    env_vars: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class TaskSpec:
    """Benchmark task definition."""
    task_id: str
    category: str
    title: str
    instruction: str
    task_dir: Path
    workspace_dir: Path
    verifier_script: Path
    requirements: TaskRequirement = field(default_factory=TaskRequirement)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return f"{self.category}/{self.task_id}"
