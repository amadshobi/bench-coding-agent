"""Trial context, execution results, and verifier outputs."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import uuid

from bca.core.types import Verdict, AgentStatus, ExecutionMetrics
from bca.core.task import TaskSpec
from bca.core.trajectory import Trajectory


@dataclass(frozen=True)
class VerifierResult:
    """Outcome of running the task verifier."""
    verdict: Verdict
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0
    error_message: Optional[str] = None


@dataclass(frozen=True)
class AgentResult:
    """Outcome of running the coding agent."""
    status: AgentStatus
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0
    trajectory: Optional[Trajectory] = None
    error_message: Optional[str] = None


@dataclass
class TrialResult:
    """Complete result of a single benchmark trial."""
    trial_id: str
    task_id: str
    category: str
    agent_id: str
    model_id: Optional[str]
    verdict: Verdict
    agent_result: AgentResult
    verifier_result: VerifierResult
    metrics: ExecutionMetrics
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trial_id": self.trial_id,
            "task_id": self.task_id,
            "category": self.category,
            "agent_id": self.agent_id,
            "model_id": self.model_id,
            "verdict": self.verdict.value,
            "agent_status": self.agent_result.status.value,
            "agent_exit_code": self.agent_result.exit_code,
            "verifier_exit_code": self.verifier_result.exit_code,
            "duration_seconds": self.metrics.duration_seconds,
            "agent_duration_seconds": self.metrics.agent_duration_seconds,
            "verifier_duration_seconds": self.metrics.verifier_duration_seconds,
            "turn_count": self.metrics.turn_count,
            "files_changed": self.metrics.diff.files_changed,
            "insertions": self.metrics.diff.insertions,
            "deletions": self.metrics.diff.deletions,
            "input_tokens": self.metrics.tokens.input_tokens,
            "output_tokens": self.metrics.tokens.output_tokens,
            "estimated_cost_usd": self.metrics.tokens.estimated_cost_usd,
            "created_at": self.created_at,
        }
