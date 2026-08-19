"""Coding agent adapter exports."""

from bca.agent.base import BaseAgent
from bca.agent.opencode import OpenCodeAgent
from bca.agent.commandcode import CommandCodeAgent
from bca.agent.antigravity import AntigravityAgent
from bca.agent.generic_cli import GenericCLIAgent
from bca.agent.factory import get_agent, AGENT_REGISTRY

__all__ = [
    "BaseAgent",
    "OpenCodeAgent",
    "CommandCodeAgent",
    "AntigravityAgent",
    "GenericCLIAgent",
    "get_agent",
    "AGENT_REGISTRY",
]
