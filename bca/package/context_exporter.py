"""
BCA Context Exporter.
Exports dataset tasks, prompts, and code solutions with smart language highlighting into Markdown context.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from bca.core.task import TaskSpec


def detect_code_language(text: str) -> Optional[str]:
    """Detects programming language from raw code string using heuristics."""
    if not text or not text.strip():
        return None

    text_str = text.strip()
    if "```" in text_str:
        return None  # Already has markdown code fences

    if re.search(r"^(def |import |from |class |@|if __name__)", text_str, re.MULTILINE) or "print(" in text_str:
        return "python"
    if re.search(r"^(function |const |let |var |export |import )", text_str, re.MULTILINE) or "console.log" in text_str:
        return "javascript"
    if re.search(r"^(package |func |import \()", text_str, re.MULTILINE):
        return "go"
    if re.search(r"^(SELECT |UPDATE |DELETE |INSERT |CREATE )", text_str, re.IGNORECASE | re.MULTILINE):
        return "sql"
    if re.search(r"^<(html|div|p|h1|!DOCTYPE)", text_str, re.IGNORECASE | re.MULTILINE):
        return "html"
    if re.search(r"^(#include |int main\(|void )", text_str, re.MULTILINE):
        return "cpp"
    if re.search(r"^(fn main\(|use |pub struct )", text_str, re.MULTILINE):
        return "rust"

    return None


def format_code_block(content: str, fallback_lang: str = "text") -> str:
    """Wraps text in appropriate markdown code fences if not already formatted."""
    if not content or not content.strip():
        return "*(empty)*"

    if "```" in content:
        return content

    lang = detect_code_language(content) or fallback_lang
    return f"```{lang}\n{content.strip()}\n```"


class ContextExporter:
    """
    Exports benchmark datasets and task suites into structured Markdown context for AI analysis.
    """

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_tasks_context(
        self,
        tasks: List[TaskSpec],
        filename: str = "benchmark_context.md",
    ) -> Path:
        target = self.output_dir / filename
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        lines = [
            "# 📚 BCA Dataset & Task Context",
            "",
            f"> Generated: `{now_str}` | Total Tasks: `{len(tasks)}`",
            "",
            "This document provides full task instructions, starter code workspaces, and verifiers for LLM analysis.",
            "",
            "---",
            "",
        ]

        for idx, task in enumerate(tasks, start=1):
            lines.extend([
                f"## 🧪 [{idx}/{len(tasks)}] Task: `{task.name}`",
                "",
                f"- **Title**: {task.title}",
                f"- **Category**: `{task.category}`",
                f"- **Timeout**: `{task.requirements.timeout_seconds}s`",
                "",
                "### 📝 Instruction / Prompt",
                "",
                task.instruction or "*(No instruction text)*",
                "",
            ])

            # Starter files preview
            if task.workspace_dir.exists():
                lines.append("### 📂 Starter Workspace Files")
                for fpath in task.workspace_dir.glob("**/*"):
                    if fpath.is_file():
                        rel = fpath.relative_to(task.workspace_dir)
                        lines.append(f"\n#### File: `{rel}`\n")
                        try:
                            code = fpath.read_text(encoding="utf-8")
                            lines.append(format_code_block(code))
                        except Exception:
                            lines.append("*(Binary file)*")

            # Verifier script preview
            if task.verifier_script and task.verifier_script.exists():
                lines.extend([
                    "",
                    f"### 🎯 Verifier Script (`{task.verifier_script.name}`)",
                    "",
                ])
                try:
                    ver_code = task.verifier_script.read_text(encoding="utf-8")
                    lines.append(format_code_block(ver_code, fallback_lang="python"))
                except Exception:
                    lines.append("*(Verifier script not readable)*")

            lines.extend(["", "---", ""])

        target.write_text("\n".join(lines), encoding="utf-8")
        return target
