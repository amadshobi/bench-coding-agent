"""OpenCode CLI agent adapter."""

import json
import shlex
from typing import Any, Dict, List, Optional

from bca.agent.base import BaseAgent
from bca.core.trajectory import Trajectory, TrajectoryStep, ToolCall, Observation


class OpenCodeAgent(BaseAgent):
    """
    Drives the `opencode` CLI agent inside the sandbox environment.
    Runs non-interactive headless mode via `opencode run "<instruction>" --auto`.
    """

    def __init__(
        self,
        agent_id: str = "opencode",
        model_id: Optional[str] = None,
        extra_env: Optional[Dict[str, str]] = None,
        flags: Optional[List[str]] = None,
        format_json: bool = True,
        auto_approve: bool = True,
        pure: bool = True,
    ):
        super().__init__(
            agent_id=agent_id,
            model_id=model_id,
            extra_env=extra_env,
            flags=flags or [],
        )
        self.format_json = format_json
        self.auto_approve = auto_approve
        self.pure = pure

    def build_command(self, instruction: str) -> str:
        parts = ["opencode", "run"]

        if self.auto_approve:
            parts.append("--auto")

        if self.pure:
            parts.append("--pure")

        if self.format_json:
            parts.append("--format=json")

        if self.model_id:
            parts.extend(["--model", shlex.quote(self.model_id)])

        for flag in self.flags:
            parts.append(flag)

        parts.append(shlex.quote(instruction))
        return " ".join(parts)

    def parse_trajectory(self, stdout: str, stderr: str) -> Trajectory:
        trajectory = Trajectory(agent_id=self.agent_id, task_id="", raw_output=stdout)
        step_num = 1

        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue

            # Try parsing JSON stream if format_json is enabled
            if line.startswith("{") and line.endswith("}"):
                try:
                    data = json.loads(line)
                    event_type = data.get("type", "")
                    if event_type in ("tool_use", "step_finish", "turn"):
                        tool = data.get("tool", "unknown")
                        args = data.get("input", {})
                        step = TrajectoryStep(
                            step_number=step_num,
                            thought=data.get("thought"),
                            tool_calls=[ToolCall(tool_name=tool, arguments=args)],
                        )
                        trajectory.add_step(step)
                        step_num += 1
                except json.JSONDecodeError:
                    pass

        return trajectory
