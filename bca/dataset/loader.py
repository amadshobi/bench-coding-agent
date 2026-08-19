"""Dataset and task loader from filesystem hierarchy."""

import json
from pathlib import Path
from typing import Dict, List, Optional

from bca.core.task import TaskSpec, TaskRequirement


class DatasetLoader:
    """
    Discovers and loads benchmark tasks from directory trees.
    Conforms to structure:
      <root>/<category>/<task_id>/
        ├── prompt.txt / instruction.md
        ├── workspace/ (starter files)
        └── verify.py / verify.sh
    """

    def __init__(self, datasets_dir: Path):
        self.datasets_dir = datasets_dir

    def list_tasks(self, category_filter: Optional[str] = None) -> List[TaskSpec]:
        """Discover all valid task suites."""
        tasks: List[TaskSpec] = []
        if not self.datasets_dir.exists():
            return tasks

        for cat_dir in self.datasets_dir.iterdir():
            if not cat_dir.is_dir() or cat_dir.name.startswith("."):
                continue

            category = cat_dir.name
            if category_filter and category != category_filter:
                continue

            for task_dir in cat_dir.iterdir():
                if not task_dir.is_dir() or task_dir.name.startswith("."):
                    continue

                task = self.load_task(category, task_dir.name)
                if task:
                    tasks.append(task)

        return sorted(tasks, key=lambda t: t.name)

    def load_task(self, category: str, task_id: str) -> Optional[TaskSpec]:
        """Load a single task spec by category and task_id."""
        task_dir = self.datasets_dir / category / task_id
        if not task_dir.is_dir():
            return None

        # Instruction file resolution
        instruction = ""
        for inst_file in ("prompt.txt", "instruction.md", "task.md"):
            p = task_dir / inst_file
            if p.is_file():
                instruction = p.read_text(encoding="utf-8").strip()
                break

        # Workspace starter dir resolution
        workspace_dir = task_dir / "workspace"
        if not workspace_dir.exists():
            workspace_dir.mkdir(parents=True, exist_ok=True)

        # Verifier script resolution
        verifier_script = None
        for ver_file in ("verify.py", "verify.sh", "test.py", "test.sh"):
            p = task_dir / ver_file
            if p.is_file():
                verifier_script = p
                break

        # Fallback dummy verifier if none specified
        if not verifier_script:
            verifier_script = task_dir / "verify.py"

        # Optional metadata (task.json)
        metadata = {}
        timeout_seconds = 180
        meta_file = task_dir / "task.json"
        if meta_file.is_file():
            try:
                metadata = json.loads(meta_file.read_text(encoding="utf-8"))
                timeout_seconds = metadata.get("timeout_seconds", timeout_seconds)
            except Exception:
                pass

        return TaskSpec(
            task_id=task_id,
            category=category,
            title=metadata.get("title", f"{category}/{task_id}"),
            instruction=instruction,
            task_dir=task_dir,
            workspace_dir=workspace_dir,
            verifier_script=verifier_script,
            requirements=TaskRequirement(timeout_seconds=timeout_seconds),
            metadata=metadata,
        )
