"""Agent factory and registry for instantiating coding agents."""

from typing import Any, Dict, List, Optional

from bca.agent.base import BaseAgent
from bca.agent.opencode import OpenCodeAgent
from bca.agent.commandcode import CommandCodeAgent
from bca.agent.omp import OMPAgent
from bca.agent.direct_gateway import DirectGatewayAgent
from bca.agent.generic_cli import GenericCLIAgent


AGENT_REGISTRY = {
    "opencode": OpenCodeAgent,
    "commandcode": CommandCodeAgent,
    "omp": OMPAgent,
    "gateway": DirectGatewayAgent,
}

AGENT_ALIASES = {
    "cmd": "commandcode",
    "oh-my-pi": "omp",
    "direct": "gateway",
    "openai": "gateway",
}


def get_agent(
    agent_id: str,
    model_id: Optional[str] = None,
    extra_env: Optional[Dict[str, str]] = None,
    flags: Optional[List[str]] = None,
    command_template: Optional[str] = None,
    **kwargs: Any,
) -> BaseAgent:
    """Instantiate a coding agent by ID or custom template."""
    normalized_id = agent_id.lower().strip()
    normalized_id = AGENT_ALIASES.get(normalized_id, normalized_id)

    if normalized_id in AGENT_REGISTRY:
        cls = AGENT_REGISTRY[normalized_id]
        return cls(
            agent_id=normalized_id,
            model_id=model_id,
            extra_env=extra_env,
            flags=flags,
            **kwargs,
        )

    if command_template:
        return GenericCLIAgent(
            agent_id=agent_id,
            command_template=command_template,
            model_id=model_id,
            extra_env=extra_env,
            flags=flags,
        )

    # Fallback to Generic CLI assumption: `<agent_id> "<instruction>"`
    return GenericCLIAgent(
        agent_id=agent_id,
        command_template=f"{agent_id} {{instruction}}",
        model_id=model_id,
        extra_env=extra_env,
        flags=flags,
    )
