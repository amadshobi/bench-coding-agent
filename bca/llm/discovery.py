"""Dynamic model discovery and auto-synchronization for BCA backends."""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


class ModelDiscovery:
    """
    Auto-discovers and synchronizes predictable model lists across 4 backends:
      1. opencode    -> from ~/.config/opencode/config.json
      2. commandcode -> from `cmd --list-models`
      3. omp         -> from ~/.omp/agent/models.yml
      4. omp-gateway -> from `gn p <provider>` active 200 OK models
    """

    @classmethod
    def get_opencode_models(cls) -> List[Dict[str, str]]:
        """Parses model definitions from ~/.config/opencode/config.json."""
        config_path = Path.home() / ".config" / "opencode" / "config.json"
        if not config_path.exists():
            return []

        models: List[Dict[str, str]] = []
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            providers = data.get("provider", {})
            for prov_name, prov_data in providers.items():
                for model_key, model_info in prov_data.get("models", {}).items():
                    full_id = f"{prov_name}/{model_key}"
                    raw_id = model_info.get("id", model_key)
                    display_name = model_info.get("name", model_key)
                    models.append({
                        "id": full_id,
                        "raw_id": raw_id,
                        "name": display_name,
                        "backend": "opencode",
                    })
        except Exception:
            pass
        return models

    @classmethod
    def get_commandcode_models(cls) -> List[Dict[str, str]]:
        """Parses models from `cmd --list-models`."""
        cmd_bin = shutil.which("cmd") or shutil.which("commandcode")
        if not cmd_bin:
            return []

        models: List[Dict[str, str]] = []
        try:
            res = subprocess.run(
                [cmd_bin, "--list-models"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            for line in res.stdout.splitlines():
                line = line.strip()
                if not line or line.startswith("Available models") or line.startswith("Open Source") or line.startswith("Anthropic") or line.startswith("OpenAI") or line.startswith("Google") or line.startswith("Sakana") or line.startswith("Meta") or line.startswith("xAI") or line.startswith("Pass the full") or line.startswith("cmd --model") or line.startswith("Docs:"):
                    continue

                parts = line.split()
                if len(parts) >= 1 and ("/" in parts[0] or parts[0].startswith("claude-") or parts[0].startswith("gpt-")):
                    model_id = parts[0]
                    desc = " ".join(parts[1:]) if len(parts) > 1 else ""
                    models.append({
                        "id": model_id,
                        "raw_id": model_id,
                        "name": desc or model_id,
                        "backend": "commandcode",
                    })
        except Exception:
            pass
        return models

    @classmethod
    def get_omp_models(cls) -> List[Dict[str, str]]:
        """Parses models from ~/.omp/agent/models.yml."""
        models_yml = Path.home() / ".omp" / "agent" / "models.yml"
        if not models_yml.exists():
            return []

        models: List[Dict[str, str]] = []
        try:
            content = models_yml.read_text(encoding="utf-8")
            current_provider = None
            for line in content.splitlines():
                # Detect provider header (e.g. "  kilo:")
                prov_match = re.match(r"^\s{2}([a-zA-Z0-9_\-]+):", line)
                if prov_match and not line.strip().startswith("providers:"):
                    current_provider = prov_match.group(1)

                # Detect model id (e.g. '      - id: "kilo-auto/small"')
                id_match = re.search(r'-\s+id:\s*["\']?([^"\']+)["\']?', line)
                if id_match and current_provider:
                    raw_id = id_match.group(1)
                    full_id = f"{current_provider}/{raw_id}" if not raw_id.startswith(f"{current_provider}/") else raw_id
                    models.append({
                        "id": full_id,
                        "raw_id": raw_id,
                        "name": raw_id,
                        "backend": "omp",
                    })
        except Exception:
            pass
        return models

    @classmethod
    def get_omp_gateway_models(cls) -> List[Dict[str, str]]:
        """
        Queries `gn p <provider>` for active 200 OK models from Goblin Nexus
        (google-antigravity, ollama-cloud, kilo, opencode-zen, openrouter).
        """
        gn_bin = shutil.which("gn")
        if not gn_bin:
            return []

        providers = ["google-antigravity", "ollama-cloud", "kilo", "opencode-zen", "openrouter"]
        models: List[Dict[str, str]] = []

        # ANSI strip regex
        ansi_regex = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

        for prov in providers:
            try:
                res = subprocess.run(
                    [gn_bin, "p", prov],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                clean_output = ansi_regex.sub("", res.stdout)
                for line in clean_output.splitlines():
                    if "200" in line and ("│" in line or "|" in line):
                        # Line format: "│ google-antigravity/claude-opus-4-6 │ 1669 ms │ 200 │"
                        parts = [p.strip() for p in re.split(r"[│|]", line) if p.strip()]
                        if len(parts) >= 3 and "200" in parts[2]:
                            model_id = parts[0]
                            latency = parts[1]
                            models.append({
                                "id": model_id,
                                "raw_id": model_id,
                                "name": f"{model_id} ({latency})",
                                "backend": "omp-gateway",
                            })
            except Exception:
                continue

        return models

    @classmethod
    def discover_all(cls) -> Dict[str, List[Dict[str, str]]]:
        """Discovers all available synchronized models across all 4 backends."""
        return {
            "opencode": cls.get_opencode_models(),
            "commandcode": cls.get_commandcode_models(),
            "omp": cls.get_omp_models(),
            "omp-gateway": cls.get_omp_gateway_models(),
        }
