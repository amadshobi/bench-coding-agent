"""Analytics Judge Agent — Evaluates coding agent solutions across quality, cleanliness, rule compliance, and efficiency."""

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from bca.core.task import TaskSpec
from bca.core.trial import AgentResult
from bca.core.types import Verdict
from bca.llm.config import BCAConfig


@dataclass
class JudgeEvaluation:
    quality_score: float = 0.0          # 0 - 100
    correctness_score: float = 0.0      # 0 - 100
    cleanliness_score: float = 0.0      # 0 - 100
    rule_compliance_score: float = 0.0  # 0 - 100
    efficiency_score: float = 0.0       # 0 - 100
    critique: str = ""
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quality_score": self.quality_score,
            "correctness_score": self.correctness_score,
            "cleanliness_score": self.cleanliness_score,
            "rule_compliance_score": self.rule_compliance_score,
            "efficiency_score": self.efficiency_score,
            "critique": self.critique,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
        }


class AnalyticsJudgeAgent:
    """
    Autonomous Judge Agent reading prompt from `config/agent/analytics.md`
    and configuration from `config/config.yml` (section `judge:`).
    Supports ANY model with flexible reasoning_effort parameter handling.
    """

    DEFAULT_PROMPT = """You are an expert Principal Software Engineer and AI Benchmark Evaluator.
Analyze the code changes (git diff), execution trajectory, and verification results.
Grade the solution strictly across:
1. Functional Correctness (0-100)
2. Code Cleanliness (0-100)
3. Engineering Discipline & Rule Compliance (0-100)
4. Efficiency & Economy (0-100)

Return ONLY a valid JSON object matching:
{
  "quality_score": 90,
  "scores": {
    "correctness": 95,
    "cleanliness": 90,
    "rule_compliance": 90,
    "efficiency": 85
  },
  "critique": "Concise summary critique.",
  "strengths": ["list of strengths"],
  "weaknesses": ["list of weaknesses"]
}
"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_id: Optional[str] = None,
        api_key: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
    ):
        cfg = BCAConfig.load_judge_config()
        self.base_url = (base_url or cfg.get("base_url") or os.environ.get("OPENAI_BASE_URL") or "http://127.0.0.1:4000/v1").rstrip("/")
        self.model_id = model_id or cfg.get("model") or "google-antigravity/gemini-3.7-flash-tiered"
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or "dummy"
        self.reasoning_effort = reasoning_effort or cfg.get("reasoning_effort") or "low"

    def _load_system_prompt(self) -> str:
        """Loads prompt from config/agent/analytics.md or fallback to analytics.example.md."""
        repo_root = Path(__file__).resolve().parents[2]
        candidates = [
            Path.cwd() / "config" / "agent" / "analytics.md",
            Path.cwd() / "config" / "agent" / "analytics.example.md",
            repo_root / "config" / "agent" / "analytics.md",
            repo_root / "config" / "agent" / "analytics.example.md",
        ]
        for p in candidates:
            if p.exists():
                try:
                    return p.read_text(encoding="utf-8").strip()
                except Exception:
                    pass
        return self.DEFAULT_PROMPT

    def evaluate(
        self,
        task: TaskSpec,
        agent_result: AgentResult,
        verdict: Verdict,
        patch_diff: str,
    ) -> JudgeEvaluation:
        """Evaluates a completed trial using LLM-as-a-Judge."""
        # Fast fallback for zero-change or failed runs
        if not patch_diff.strip() and verdict == Verdict.FAIL:
            return JudgeEvaluation(
                quality_score=10.0,
                correctness_score=0.0,
                cleanliness_score=50.0,
                rule_compliance_score=50.0,
                efficiency_score=0.0,
                critique="Agent failed to produce any code patch or resolve the issue.",
                weaknesses=["No code modifications produced"],
            )

        system_prompt = self._load_system_prompt()
        user_prompt = f"""### TASK SPECIFICATION:
ID: {task.task_id}
Category: {task.category}
Title: {task.title}
Instruction: {task.instruction}

### VERDICT:
Outcome: {verdict.value}

### GIT DIFF PRODUCED BY AGENT:
```diff
{patch_diff[:4000] if patch_diff else 'No diff'}
```

### AGENT LOGS SUMMARY:
```
{agent_result.stdout[-1500:] if agent_result.stdout else 'No stdout'}
```

Please evaluate this solution now according to your grading criteria and output strict JSON."""

        try:
            payload: Dict[str, Any] = {
                "model": self.model_id,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }

            # If model supports or requires reasoning effort (e.g. Gemini 3.7 / reasoning models)
            if self.reasoning_effort:
                payload["reasoning_effort"] = self.reasoning_effort

            req = urllib.request.Request(
                f"{self.base_url}/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                raw_text = resp_data["choices"][0]["message"]["content"].strip()

                # Clean markdown wrapper if present
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.startswith("```"):
                    raw_text = raw_text[3:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]

                data = json.loads(raw_text.strip())
                scores = data.get("scores", {})

                return JudgeEvaluation(
                    quality_score=float(data.get("quality_score", 75.0)),
                    correctness_score=float(scores.get("correctness", 80.0)),
                    cleanliness_score=float(scores.get("cleanliness", 80.0)),
                    rule_compliance_score=float(scores.get("rule_compliance", 80.0)),
                    efficiency_score=float(scores.get("efficiency", 80.0)),
                    critique=str(data.get("critique", "Evaluation completed.")),
                    strengths=list(data.get("strengths", [])),
                    weaknesses=list(data.get("weaknesses", [])),
                )

        except Exception as exc:
            # Fallback heuristic calculation if endpoint is offline
            is_pass = (verdict == Verdict.PASS)
            base_score = 85.0 if is_pass else 35.0
            return JudgeEvaluation(
                quality_score=base_score,
                correctness_score=90.0 if is_pass else 20.0,
                cleanliness_score=80.0,
                rule_compliance_score=85.0,
                efficiency_score=80.0,
                critique=f"Deterministic fallback grading ({verdict.value}). Offline judge: {exc}",
                strengths=["Automated test passed" if is_pass else "Captured failure telemetry"],
                weaknesses=["Judge offline fallback invoked"],
            )
