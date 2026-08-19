"""
BCA Benchmark Summarizer & Reporter.
Calculates deterministic aggregates, rankings, dual currency (USD/IDR), and failure breakdowns.
"""

from __future__ import annotations

import csv
import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional

from bca.core.trial import TrialResult
from bca.core.types import Verdict

logger = logging.getLogger(__name__)

# USD to IDR static exchange rate for reporting
USD_TO_IDR = 16250.0


def format_currency_usd(value: float) -> str:
    """Format USD currency."""
    return f"${value:,.6f}"


def format_currency_idr(value: float) -> str:
    """Format IDR currency."""
    idr_val = value * USD_TO_IDR
    return f"Rp {idr_val:,.2f}"


def simplify_failure_reason(raw_error: str) -> str:
    """Categorize and simplify raw errors into concise readable badges."""
    if not raw_error:
        return "Unknown error"
    lower = raw_error.lower()
    if "timeout" in lower or "timed out" in lower:
        return "⏱️ Execution Timeout"
    if "syntaxerror" in lower or "invalid syntax" in lower:
        return "❌ Syntax Error"
    if "zerodivisionerror" in lower:
        return "💥 Zero Division Exception"
    if "assertionerror" in lower:
        return "🧪 Test Assertion Failed"
    if "permission denied" in lower or "read-only" in lower:
        return "🛡️ Sandbox Permission Blocked"
    return f"⚠️ {raw_error[:60]}"


class BenchmarkSummarizer:
    """
    Generates rich, human-readable benchmark summaries in Markdown.
    """

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_summary_markdown(
        self,
        trials: List[TrialResult],
        filename: str = "results.md",
    ) -> Path:
        target = self.output_dir / filename
        total = len(trials)
        if total == 0:
            target.write_text("# 🏆 BCA Benchmark Results\n\nNo trials recorded.\n", encoding="utf-8")
            return target

        passed = sum(1 for t in trials if t.verdict == Verdict.PASS)
        failed = sum(1 for t in trials if t.verdict != Verdict.PASS)
        pass_rate = round((passed / total) * 100.0, 1)

        durations = [t.metrics.duration_seconds for t in trials]
        avg_dur = round(mean(durations), 2) if durations else 0.0

        total_cost_usd = sum(t.metrics.tokens.estimated_cost_usd for t in trials)
        total_tokens = sum(t.metrics.tokens.total_tokens for t in trials)

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # Grouping by Agent & Model
        agent_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total": 0, "passed": 0, "durations": [], "cost": 0.0, "insertions": 0, "deletions": 0
        })

        for t in trials:
            key = f"{t.agent_id} ({t.model_id or 'default'})"
            st = agent_stats[key]
            st["total"] += 1
            if t.verdict == Verdict.PASS:
                st["passed"] += 1
            st["durations"].append(t.metrics.duration_seconds)
            st["cost"] += t.metrics.tokens.estimated_cost_usd
            st["insertions"] += t.metrics.diff.insertions
            st["deletions"] += t.metrics.diff.deletions

        lines = [
            "# 🏆 BCA (Bench Coding Agent) Evaluation Report",
            "",
            f"> Generated: `{now_str}`",
            "",
            "## 📊 Executive Summary",
            "",
            f"- **Total Benchmark Trials**: `{total}`",
            f"- **Overall Pass Rate**: **`{pass_rate}%`** ({passed}/{total} Passed, {failed} Failed)",
            f"- **Average Duration**: `{avg_dur}s`",
            f"- **Total Token Consumption**: `{total_tokens:,}` tokens",
            f"- **Total Estimated Cost**: `{format_currency_usd(total_cost_usd)}` ({format_currency_idr(total_cost_usd)})",
            "",
            "---",
            "",
            "## 🥇 Agent & Model Leaderboard",
            "",
            "| Rank | Agent / Model | Pass Rate | Passed / Total | Avg Duration | Diff (+/-) | Est. Cost (USD) | Est. Cost (IDR) |",
            "|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|",
        ]

        sorted_agents = sorted(
            agent_stats.items(),
            key=lambda x: (x[1]["passed"] / x[1]["total"] if x[1]["total"] else 0, -mean(x[1]["durations"] or [0])),
            reverse=True,
        )

        for rank, (name, st) in enumerate(sorted_agents, start=1):
            rate = round((st["passed"] / st["total"] * 100.0) if st["total"] else 0.0, 1)
            avg_d = round(mean(st["durations"]), 2) if st["durations"] else 0.0
            diff_str = f"+{st['insertions']}/-{st['deletions']}"
            lines.append(
                f"| {rank} | **{name}** | **`{rate}%`** | {st['passed']}/{st['total']} | `{avg_d}s` | `{diff_str}` | `{format_currency_usd(st['cost'])}` | `{format_currency_idr(st['cost'])}` |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## 🧪 Detailed Trial Breakdown",
            "",
            "| Trial ID | Category | Task | Agent | Verdict | Duration | Diff (+/-) | Notes / Error |",
            "|---|---|---|---|:---:|---|---|---|",
        ])

        for t in trials:
            diff_str = f"+{t.metrics.diff.insertions}/-{t.metrics.diff.deletions}"
            icon = "✅ **PASS**" if t.verdict == Verdict.PASS else "❌ **FAIL**"
            agent_label = f"{t.agent_id}" + (f":{t.model_id}" if t.model_id else "")
            err_msg = ""
            if t.verdict != Verdict.PASS:
                err_msg = simplify_failure_reason(t.verifier_result.stderr or t.verifier_result.stdout or t.agent_result.stderr)

            lines.append(
                f"| `{t.trial_id[:8]}` | `{t.category}` | **{t.task_id}** | `{agent_label}` | {icon} | `{t.metrics.duration_seconds}s` | `{diff_str}` | {err_msg} |"
            )

        lines.append("")
        target.write_text("\n".join(lines), encoding="utf-8")
        return target
