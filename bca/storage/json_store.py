"""JSON file storage and cache for BCA."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from bca.core.trial import TrialResult


class JSONStorage:
    """
    Appends and manages trial results in structured JSON files.
    """

    def __init__(self, json_path: Path):
        self.json_path = json_path
        self.json_path.parent.mkdir(parents=True, exist_ok=True)

    def save_trial(self, result: TrialResult) -> None:
        data = self.load_all()
        data.append(result.to_dict())
        self.json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load_all(self) -> List[Dict[str, Any]]:
        if not self.json_path.exists():
            return []
        try:
            return json.loads(self.json_path.read_text(encoding="utf-8"))
        except Exception:
            return []
