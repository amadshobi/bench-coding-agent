"""SQLite storage engine for trial runs, verdicts, and metrics persistence."""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from bca.core.trial import TrialResult


class SQLiteStorage:
    """
    Persists benchmark trial executions, metrics, and verdicts into a local SQLite database.
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trials (
                    trial_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    model_id TEXT,
                    verdict TEXT NOT NULL,
                    agent_status TEXT NOT NULL,
                    agent_exit_code INTEGER NOT NULL,
                    verifier_exit_code INTEGER NOT NULL,
                    duration_seconds REAL NOT NULL,
                    agent_duration_seconds REAL NOT NULL,
                    verifier_duration_seconds REAL NOT NULL,
                    turn_count INTEGER NOT NULL,
                    files_changed INTEGER NOT NULL,
                    insertions INTEGER NOT NULL,
                    deletions INTEGER NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    estimated_cost_usd REAL NOT NULL,
                    estimated_cost_idr REAL DEFAULT 0.0,
                    quality_score REAL DEFAULT 0.0,
                    critique TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    extra_data TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trials_task ON trials(task_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trials_agent ON trials(agent_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trials_verdict ON trials(verdict)")
            conn.commit()

    def save_trial(self, result: TrialResult) -> None:
        """Insert or replace a trial record."""
        data = result.to_dict()
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO trials (
                    trial_id, task_id, category, agent_id, model_id,
                    verdict, agent_status, agent_exit_code, verifier_exit_code,
                    duration_seconds, agent_duration_seconds, verifier_duration_seconds,
                    turn_count, files_changed, insertions, deletions,
                    input_tokens, output_tokens, estimated_cost_usd, estimated_cost_idr,
                    quality_score, critique, created_at, extra_data
                ) VALUES (
                    :trial_id, :task_id, :category, :agent_id, :model_id,
                    :verdict, :agent_status, :agent_exit_code, :verifier_exit_code,
                    :duration_seconds, :agent_duration_seconds, :verifier_duration_seconds,
                    :turn_count, :files_changed, :insertions, :deletions,
                    :input_tokens, :output_tokens, :estimated_cost_usd, :estimated_cost_idr,
                    :quality_score, :critique, :created_at, :extra_data
                )
                """,
                {
                    **data,
                    "extra_data": json.dumps({
                        "stdout_snippet": result.agent_result.stdout[-500:],
                        "verifier_stdout": result.verifier_result.stdout[-500:],
                    }),
                },
            )
            conn.commit()

    def list_trials(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve recent trial records."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM trials ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_summary_stats(self) -> Dict[str, Any]:
        """Calculate overall pass rates and execution totals."""
        with self._get_conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM trials").fetchone()[0]
            passed = conn.execute("SELECT COUNT(*) FROM trials WHERE verdict = 'PASS'").fetchone()[0]
            failed = conn.execute("SELECT COUNT(*) FROM trials WHERE verdict = 'FAIL'").fetchone()[0]
            avg_duration = conn.execute("SELECT AVG(duration_seconds) FROM trials").fetchone()[0] or 0.0

            return {
                "total_runs": total,
                "passed": passed,
                "failed": failed,
                "pass_rate_pct": round((passed / total * 100) if total > 0 else 0.0, 2),
                "avg_duration_seconds": round(avg_duration, 2),
            }
