"""Lightweight terminal UI and interactive inspector for BCA benchmark results."""

import sys
import shutil
from pathlib import Path
from typing import Optional

from bca.storage.sqlite import SQLiteStorage


def render_tui_dashboard(db_path: Optional[Path] = None, limit: int = 15) -> None:
    """Renders a formatted terminal dashboard with live metrics and recent trials."""
    db_file = db_path or Path.cwd() / "results" / "bca.sqlite3"
    if not db_file.exists():
        print("ℹ️ [BCA TUI] No benchmark database found at results/bca.sqlite3")
        return

    storage = SQLiteStorage(db_file)
    stats = storage.get_summary_stats()
    trials = storage.list_trials(limit=limit)

    term_width = shutil.get_terminal_size((80, 24)).columns
    border = "═" * min(term_width, 80)
    thin_border = "─" * min(term_width, 80)

    print("\n" + border)
    print(" 🚀 BCA (BENCH CODING AGENT) — TERMINAL DASHBOARD")
    print(border)
    print(
        f"  Total Trials : {stats['total_runs']:<5} | "
        f"Passed : {stats['passed']:<5} | "
        f"Pass Rate : {stats['pass_rate_pct']}% | "
        f"Avg Duration : {stats['avg_duration_seconds']}s"
    )
    print(thin_border)
    print(f" {'TRIAL':<9} │ {'CATEGORY':<10} │ {'TASK':<18} │ {'AGENT':<12} │ {'STATUS':<8} │ {'DURATION'}")
    print(thin_border)

    for t in trials:
        tid = t["trial_id"][:8]
        status = "✅ PASS" if t["verdict"] == "PASS" else "❌ FAIL"
        task_name = t["task_id"][:18]
        agent_name = t["agent_id"][:12]
        cat = t["category"][:10]
        dur = f"{t['duration_seconds']}s"
        print(f" {tid:<9} │ {cat:<10} │ {task_name:<18} │ {agent_name:<12} │ {status:<8} │ {dur}")

    print(border + "\n")
