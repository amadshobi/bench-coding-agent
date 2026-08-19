"""CommandCode CLI agent adapter."""

import shlex
from typing import Any, Dict, List, Optional

from bca.agent.base import BaseAgent


class CommandCodeAgent(BaseAgent):
    """
    Drives the `commandcode` CLI agent inside the sandbox environment.
    """

    def __init__(
        self,
        agent_id: str = "commandcode",
        model_id: Optional[str] = None,
        extra_env: Optional[Dict[str, str]] = None,
        flags: Optional[List[str]] = None,
    ):
        super().__init__(
            agent_id=agent_id,
            model_id=model_id,
            extra_env=extra_env,
            flags=flags or [],
        )

    def build_command(self, instruction: str) -> str:
        parts = ["commandcode", "--prompt", shlex.quote(instruction)]

        if self.model_id:
            parts.extend(["--model", shlex.quote(self.model_id)])

        for flag in self.flags:
            parts.append(flag)

        return " ".join(parts)
