"""Abstract base class for coding agent adapters."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import time

from bca.core.types import AgentStatus
from bca.core.trial import AgentResult
from bca.core.trajectory import Trajectory
from bca.sandbox.base import BaseSandbox, ProcessResult


class BaseAgent(ABC):
    """
    Abstract adapter for driving autonomous coding agents inside a sandbox.
    """

    def __init__(
        self,
        agent_id: str,
        model_id: Optional[str] = None,
        extra_env: Optional[Dict[str, str]] = None,
        flags: Optional[List[str]] = None,
    ):
        self.agent_id = agent_id
        self.model_id = model_id
        self.extra_env = extra_env or {}
        self.flags = flags or []

    @abstractmethod
    def build_command(self, instruction: str) -> str:
        """Construct the CLI command string to invoke the agent."""
        ...

    def setup(self, sandbox: BaseSandbox) -> None:
        """Optional hook to install or configure agent prerequisites inside the sandbox."""
        pass

    def run(
        self,
        instruction: str,
        sandbox: BaseSandbox,
        timeout_seconds: int = 300,
    ) -> AgentResult:
        """Executes the agent command inside the sandbox and captures output."""
        start_time = time.perf_counter()
        cmd = self.build_command(instruction)

        # Run inside sandbox
        proc_res: ProcessResult = sandbox.exec(
            cmd=cmd,
            timeout_seconds=timeout_seconds,
            extra_env=self.extra_env,
        )
        duration = time.perf_counter() - start_time

        if proc_res.timed_out:
            status = AgentStatus.TIMEOUT
        elif proc_res.exit_code == 0:
            status = AgentStatus.COMPLETED
        else:
            status = AgentStatus.FAILED

        trajectory = self.parse_trajectory(proc_res.stdout, proc_res.stderr)

        return AgentResult(
            status=status,
            exit_code=proc_res.exit_code,
            stdout=proc_res.stdout,
            stderr=proc_res.stderr,
            duration_seconds=round(duration, 3),
            trajectory=trajectory,
            error_message=proc_res.stderr if status == AgentStatus.FAILED else None,
        )

    def parse_trajectory(self, stdout: str, stderr: str) -> Trajectory:
        """Parse raw stdout into structured Trajectory. Override in subclass for format parsing."""
        return Trajectory(
            agent_id=self.agent_id,
            task_id="",
            raw_output=stdout,
        )
