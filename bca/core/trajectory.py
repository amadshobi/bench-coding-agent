"""Trajectory and step history recording for agent execution."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


@dataclass(frozen=True)
class ToolCall:
    """Tool invocation by the agent."""
    tool_name: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    raw_input: Optional[str] = None


@dataclass(frozen=True)
class Observation:
    """Observation/output returned from tool or environment."""
    output: str
    exit_code: int = 0
    error: Optional[str] = None


@dataclass(frozen=True)
class TrajectoryStep:
    """Single turn/step in an agent trajectory."""
    step_number: int
    thought: Optional[str] = None
    tool_calls: List[ToolCall] = field(default_factory=list)
    observations: List[Observation] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Trajectory:
    """Complete trace of an agent's problem-solving attempt."""
    agent_id: str
    task_id: str
    steps: List[TrajectoryStep] = field(default_factory=list)
    raw_output: str = ""

    def add_step(self, step: TrajectoryStep) -> None:
        self.steps.append(step)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "steps": [
                {
                    "step_number": s.step_number,
                    "thought": s.thought,
                    "tool_calls": [
                        {"tool": tc.tool_name, "args": tc.arguments, "raw": tc.raw_input}
                        for tc in s.tool_calls
                    ],
                    "observations": [
                        {"output": obs.output, "exit_code": obs.exit_code, "error": obs.error}
                        for obs in s.observations
                    ],
                    "timestamp": s.timestamp,
                }
                for s in self.steps
            ],
            "raw_output": self.raw_output,
        }
