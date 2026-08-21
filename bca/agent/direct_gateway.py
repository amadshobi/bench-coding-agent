"""Direct OpenAI-Compatible Gateway Agent (Direct LLM Loop without CLI Agent Wrappers)."""

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from bca.agent.base import BaseAgent
from bca.core.types import AgentStatus
from bca.core.trial import AgentResult
from bca.core.trajectory import Trajectory, TrajectoryStep, ToolCall, Observation
from bca.sandbox.base import BaseSandbox, ProcessResult

SYSTEM_PROMPT = """You are an expert autonomous coding assistant.
You are running in a sandbox environment to solve software engineering tasks.
You have access to tools to inspect, read, edit, write files, and execute bash commands.
Always solve the requested issue completely and verify your solution before finishing.
When you are done, return a concise summary of your work.
"""

TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Execute a bash shell command in the workspace directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The command to run"}
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the text content of a file in the workspace",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative file path"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write or overwrite content to a file in the workspace",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative file path"},
                    "content": {"type": "string", "description": "Full file content to write"},
                },
                "required": ["path", "content"],
            },
        },
    },
]


class DirectGatewayAgent(BaseAgent):
    """
    Executes a direct OpenAI-compatible tool loop (e.g. against omp-gateway http://127.0.0.1:4000/v1
    or OpenRouter/OpenAI endpoints) without any external CLI agent wrapper.
    Evaluates pure model intelligence and function-calling capabilities.
    """

    def __init__(
        self,
        agent_id: str = "gateway",
        model_id: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        max_turns: int = 15,
        extra_env: Optional[Dict[str, str]] = None,
        flags: Optional[List[str]] = None,
    ):
        super().__init__(
            agent_id=agent_id,
            model_id=model_id or "google-antigravity/gemini-3.7-flash-tiered",
            extra_env=extra_env,
            flags=flags or [],
        )
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL") or "http://127.0.0.1:4000/v1").rstrip("/")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or "dummy"
        self.max_turns = max_turns

    def build_command(self, instruction: str) -> str:
        """Unused in direct API mode, but returns representation."""
        return f"direct-gateway://{self.base_url}/chat/completions?model={self.model_id}"

    def _call_llm(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Makes an HTTP POST request to the OpenAI-compatible endpoint."""
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model_id,
            "messages": messages,
            "tools": TOOLS_SPEC,
            "tool_choice": "auto",
            "temperature": 0.1,
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]

    def run(
        self,
        instruction: str,
        sandbox: BaseSandbox,
        timeout_seconds: int = 300,
    ) -> AgentResult:
        start_time = time.perf_counter()
        trajectory = Trajectory(agent_id=self.agent_id, task_id="")
        logs: List[str] = []

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": instruction},
        ]

        turn = 0
        error_msg = None

        try:
            while turn < self.max_turns:
                turn += 1
                if (time.perf_counter() - start_time) > timeout_seconds:
                    return AgentResult(
                        status=AgentStatus.TIMEOUT,
                        exit_code=124,
                        stdout="\n".join(logs),
                        duration_seconds=round(time.perf_counter() - start_time, 3),
                        trajectory=trajectory,
                        error_message=f"Direct LLM run exceeded timeout ({timeout_seconds}s)",
                    )

                assistant_msg = self._call_llm(messages)
                messages.append(assistant_msg)

                content = assistant_msg.get("content") or ""
                tool_calls = assistant_msg.get("tool_calls") or []

                if content:
                    logs.append(f"[Assistant] {content}")

                if not tool_calls:
                    # Model finished thinking and answered
                    break

                for tc in tool_calls:
                    func = tc.get("function", {})
                    name = func.get("name")
                    call_id = tc.get("id", f"call_{turn}")
                    try:
                        args = json.loads(func.get("arguments", "{}"))
                    except Exception:
                        args = {}

                    # Record trajectory
                    step = TrajectoryStep(
                        step_number=turn,
                        thought=content if content else None,
                        tool_calls=[ToolCall(tool_name=name, arguments=args)],
                    )

                    # Execute tool against sandbox
                    output = ""
                    if name == "bash":
                        cmd = args.get("command", "")
                        pres = sandbox.exec(cmd, timeout_seconds=60)
                        output = pres.stdout + (f"\nSTDERR:\n{pres.stderr}" if pres.stderr else "")
                    elif name == "read_file":
                        p = args.get("path", "")
                        try:
                            output = sandbox.read_file(p)
                        except Exception as e:
                            output = f"Error reading file: {e}"
                    elif name == "write_file":
                        p = args.get("path", "")
                        c = args.get("content", "")
                        try:
                            sandbox.write_file(p, c)
                            output = f"Successfully wrote {len(c)} bytes to {p}"
                        except Exception as e:
                            output = f"Error writing file: {e}"
                    else:
                        output = f"Unknown tool: {name}"

                    step.observations.append(Observation(tool_name=name, output=output[:1500]))
                    trajectory.add_step(step)
                    logs.append(f"[Tool: {name}] -> {output[:300]}")

                    # Append tool result back to conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": output,
                    })

            duration = round(time.perf_counter() - start_time, 3)
            return AgentResult(
                status=AgentStatus.COMPLETED,
                exit_code=0,
                stdout="\n".join(logs),
                duration_seconds=duration,
                trajectory=trajectory,
            )

        except Exception as exc:
            duration = round(time.perf_counter() - start_time, 3)
            return AgentResult(
                status=AgentStatus.FAILED,
                exit_code=1,
                stdout="\n".join(logs),
                duration_seconds=duration,
                trajectory=trajectory,
                error_message=str(exc),
            )
