"""Generic configurable CLI agent adapter."""

import shlex
from typing import Any, Dict, List, Optional

from bca.agent.base import BaseAgent


class GenericCLIAgent(BaseAgent):
    """
    Adapter for any command-line coding agent (Claude Code, Aider, Codex, etc.).
    Uses a template string where `{instruction}` is substituted.
    """

    def __init__(
        self,
        agent_id: str,
        command_template: str,
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
        self.command_template = command_template

    def build_command(self, instruction: str) -> str:
        safe_instruction = shlex.quote(instruction)
        cmd = self.command_template.format(
            instruction=safe_instruction,
            model=shlex.quote(self.model_id or ""),
        )
        if self.flags:
            cmd = f"{cmd} {' '.join(self.flags)}"
        return cmd
