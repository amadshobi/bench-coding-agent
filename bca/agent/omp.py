"""Oh My Pi (omp) CLI agent adapter."""

import json
import shlex
import shutil
from typing import Any, Dict, List, Optional

from bca.agent.base import BaseAgent
from bca.core.trajectory import Trajectory, TrajectoryStep, ToolCall


class OMPAgent(BaseAgent):
    """
    Drives the `omp` (Oh My Pi) CLI agent inside the sandbox environment.
    Runs non-interactive headless mode via `omp -p "<instruction>" --auto-approve --no-session`.
    """

    def __init__(
        self,
        agent_id: str = "omp",
        model_id: Optional[str] = None,
        extra_env: Optional[Dict[str, str]] = None,
        flags: Optional[List[str]] = None,
        auto_approve: bool = True,
        mode: str = "json",
    ):
        super().__init__(
            agent_id=agent_id,
            model_id=model_id,
            extra_env=extra_env,
            flags=flags or [],
        )
        self.auto_approve = auto_approve
        self.mode = mode

    def build_command(self, instruction: str) -> str:
        parts = ["omp", "-p", shlex.quote(instruction), "--no-session"]

        if self.auto_approve:
            parts.append("--auto-approve")

        if self.mode:
            parts.append(f"--mode={self.mode}")

        if self.model_id:
            parts.append(f"--model={shlex.quote(self.model_id)}")

        for flag in self.flags:
            parts.append(flag)

        return " ".join(parts)

    def parse_trajectory(self, stdout: str, stderr: str) -> Trajectory:
        trajectory = Trajectory(agent_id=self.agent_id, task_id="", raw_output=stdout)
        step_num = 1

        for line in stdout.splitlines():
            line = line.strip()
            if not line or not line.startswith("{") or not line.endswith("}"):
                continue

            try:
                data = json.loads(line)
                event_type = data.get("type") or data.get("event", "")
                if event_type in ("tool_use", "tool_call", "step", "message"):
                    tool_name = data.get("tool") or data.get("name") or "tool"
                    args = data.get("input") or data.get("args", {})
                    thought = data.get("thought") or data.get("text")
                    step = TrajectoryStep(
                        step_number=step_num,
                        thought=thought,
                        tool_calls=[
                            ToolCall(
                                tool_name=str(tool_name),
                                arguments=args if isinstance(args, dict) else {"arg": args},
                            )
                        ],
                    )
                    trajectory.add_step(step)
                    step_num += 1
            except json.JSONDecodeError:
                pass

        return trajectory
