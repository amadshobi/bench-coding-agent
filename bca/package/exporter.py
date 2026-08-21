"""Exporting and packaging benchmark results into CSV and Markdown."""

import csv
from pathlib import Path
from typing import Any, Dict, List

from bca.core.trial import TrialResult


class ResultExporter:
    """
    Exports trial results into standard CSV ranking reports and Markdown summaries.
    """

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_csv(self, trials: List[TrialResult], filename: str = "bca_results.csv") -> Path:
        target = self.output_dir / filename
        if not trials:
            return target

        fieldnames = [
            "trial_id",
            "task_id",
            "category",
            "agent_id",
            "model_id",
            "verdict",
            "agent_status",
            "agent_exit_code",
            "verifier_exit_code",
            "duration_seconds",
            "agent_duration_seconds",
            "verifier_duration_seconds",
            "turn_count",
            "files_changed",
            "insertions",
            "deletions",
            "input_tokens",
            "output_tokens",
            "estimated_cost_usd",
            "estimated_cost_idr",
            "quality_score",
            "critique",
            "created_at",
        ]

        with open(target, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for t in trials:
                writer.writerow(t.to_dict())

        return target

    def export_markdown_summary(self, trials: List[TrialResult], filename: str = "results.md") -> Path:
        target = self.output_dir / filename
        total = len(trials)
        passed = sum(1 for t in trials if t.verdict.value == "PASS")
        pass_rate = round((passed / total * 100) if total > 0 else 0.0, 1)

        lines = [
            "# 🏆 BCA (Bench Coding Agent) Results",
            "",
            f"**Total Trials:** {total} | **Passed:** {passed} | **Pass Rate:** {pass_rate}%",
            "",
            "| Trial ID | Category | Task | Agent | Model | Verdict | Duration | Diff (+/-) |",
            "|---|---|---|---|---|---|---|---|",
        ]

        for t in trials:
            diff_str = f"+{t.metrics.diff.insertions}/-{t.metrics.diff.deletions}"
            icon = "✅" if t.verdict.value == "PASS" else "❌"
            model_str = t.model_id or "-"
            lines.append(
                f"| `{t.trial_id[:8]}` | `{t.category}` | **{t.task_id}** | `{t.agent_id}` | `{model_str}` | {icon} {t.verdict.value} | {t.metrics.duration_seconds}s | `{diff_str}` |"
            )

        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return target
