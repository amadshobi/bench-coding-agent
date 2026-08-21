"""Beautiful Multi-Dimensional CLI Reporting and Leaderboard Renderer for BCA."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from bca.storage.sqlite import SQLiteStorage
from bca.package.terminal_renderer import render_terminal_markdown
from bca.package.ui import TerminalUI


class ReportCLI:
    """Renders Leaderboard (-b), Terminal Markdown (-md), and Pure JSON (--json)."""

    @classmethod
    def render_leaderboard(cls, db_path: Path, limit: int = 20) -> None:
        """Renders 4-dimensional leaderboard (Overall, Pass Rate, Quality Score, Avg Time, Avg Cost)."""
        if not db_path.exists():
            print("ℹ️ No benchmark trials found in database.")
            return

        storage = SQLiteStorage(db_path)
        trials = storage.list_trials(limit=500)
        if not trials:
            print("ℹ️ No benchmark trial records found.")
            return

        # Aggregate stats per (agent_id, model_id)
        matrix: Dict[str, Dict[str, Any]] = {}
        for t in trials:
            key = f"{t['agent_id']}::{t.get('model_id') or 'default'}"
            if key not in matrix:
                matrix[key] = {
                    "agent": t["agent_id"],
                    "model": t.get("model_id") or "default",
                    "total": 0,
                    "passed": 0,
                    "durations": [],
                    "costs_idr": [],
                    "qualities": [],
                    "critiques": [],
                }
            matrix[key]["total"] += 1
            if t["verdict"] == "PASS":
                matrix[key]["passed"] += 1
            matrix[key]["durations"].append(float(t.get("duration_seconds", 0)))
            matrix[key]["costs_idr"].append(float(t.get("estimated_cost_idr", 0)))
            q_score = float(t.get("quality_score", 0))
            if q_score > 0:
                matrix[key]["qualities"].append(q_score)
            if t.get("critique"):
                matrix[key]["critiques"].append(t["critique"])

        # Calculate Rankings & Overall Score
        rank_list = []
        for key, d in matrix.items():
            pass_rate = (d["passed"] / d["total"] * 100) if d["total"] > 0 else 0.0
            avg_time = sum(d["durations"]) / len(d["durations"]) if d["durations"] else 0.0
            avg_cost_idr = sum(d["costs_idr"]) / len(d["costs_idr"]) if d["costs_idr"] else 0.0
            avg_quality = sum(d["qualities"]) / len(d["qualities"]) if d["qualities"] else (85.0 if pass_rate == 100 else 40.0)

            # Overall Score Formula:
            # 50% Pass Rate + 25% Quality + 15% Speed + 10% Cost
            speed_score = max(0.0, 100.0 - (avg_time * 2.0))
            cost_score = max(0.0, 100.0 - (avg_cost_idr / 50.0))
            overall = (pass_rate * 0.50) + (avg_quality * 0.25) + (speed_score * 0.15) + (cost_score * 0.10)

            rank_list.append({
                "agent": d["agent"],
                "model": d["model"],
                "overall": round(overall, 1),
                "pass_rate_pct": round(pass_rate, 1),
                "passed": d["passed"],
                "total": d["total"],
                "quality": round(avg_quality, 1),
                "avg_time": round(avg_time, 2),
                "avg_cost_idr": round(avg_cost_idr, 1),
            })

        # Sort by Overall Score descending
        rank_list.sort(key=lambda x: x["overall"], reverse=True)

        headers = ["Rank", "Agent", "Target Model", "Overall", "Pass Rate", "Quality", "Avg Time", "Cost (IDR)"]
        alignments = ["center", "left", "left", "right", "left", "right", "right", "right"]
        rows = []

        for idx, r in enumerate(rank_list[:limit], start=1):
            m_name = r['model'].split('/')[-1] if '/' in r['model'] else r['model']
            pass_badge = f"\x1b[32m{r['pass_rate_pct']}%\x1b[0m ({r['passed']}/{r['total']})" if r['pass_rate_pct'] == 100 else f"\x1b[31m{r['pass_rate_pct']}%\x1b[0m ({r['passed']}/{r['total']})"
            cost_str = f"Rp {r['avg_cost_idr']:,.0f}" if r['avg_cost_idr'] > 0 else "\x1b[32mFree\x1b[0m"
            rank_badge = f"\x1b[1;33m#{idx}\x1b[0m" if idx == 1 else f"#{idx}"

            rows.append([
                rank_badge,
                f"\x1b[36m{r['agent']}\x1b[0m",
                f"\x1b[1;37m{m_name[:26]}\x1b[0m",
                f"\x1b[1;33m{r['overall']:>5.1f}\x1b[0m/100",
                pass_badge,
                f"⭐ {r['quality']:>4.1f}",
                f"{r['avg_time']:>4.1f}s",
                cost_str,
            ])

        print("\n" + TerminalUI.render_table(headers, rows, alignments=alignments, title="🏆 BCA BENCHMARK LEADERBOARD (4-DIMENSIONS EVAL)"))
        print("\x1b[90m💡 Formula: 50% Pass Rate + 25% Judge Quality + 15% Speed + 10% Cost Efficiency\x1b[0m\n")

    @classmethod
    def render_markdown(cls, results_dir: Path) -> None:
        """Renders results/results.md directly in terminal with styled formatting."""
        md_file = results_dir / "results.md"
        if not md_file.exists():
            print(f"ℹ️ No summary report found at '{md_file}'. Run a benchmark first.")
            return

        raw_content = md_file.read_text(encoding="utf-8")
        rendered = render_terminal_markdown(raw_content)
        print("\n" + rendered + "\n")

    @classmethod
    def render_json(cls, db_path: Path, limit: int = 100) -> None:
        """Outputs pure machine-readable JSON."""
        if not db_path.exists():
            print(json.dumps({"error": "No database found", "trials": []}))
            return

        storage = SQLiteStorage(db_path)
        trials = storage.list_trials(limit=limit)
        stats = storage.get_summary_stats()
        print(json.dumps({"stats": stats, "trials": trials}, indent=2))
