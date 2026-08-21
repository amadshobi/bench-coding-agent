"""Configuration loader for BCA backends and model aliases."""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class BCAConfig:
    """Loads and resolves models from config/config.yml or config/config.example.yml."""

    @classmethod
    def find_config_path(cls) -> Optional[Path]:
        """Looks for config.yml or config.example.yml in root or config/ directory."""
        candidates = [
            Path.cwd() / "config" / "config.yml",
            Path.cwd() / "config" / "models.yml",
            Path.cwd() / "config.yml",
            Path.cwd() / "config" / "config.example.yml",
        ]
        for p in candidates:
            if p.exists():
                return p
        return None

    @classmethod
    def _simple_yaml_parse(cls, content: str) -> Dict[str, Dict[str, str]]:
        """Lightweight zero-dependency YAML parser for key-value nested structures."""
        backends: Dict[str, Dict[str, str]] = {}
        current_backend = None

        for line in content.splitlines():
            # Strip comments & whitespace
            line = line.split("#", 1)[0].rstrip()
            if not line.strip() or line.strip() == "backends:":
                continue

            # Check backend key (indent: 2 spaces, e.g. "  opencode:")
            b_match = re.match(r"^  ([a-zA-Z0-9_\-]+):", line)
            if b_match:
                current_backend = b_match.group(1)
                backends[current_backend] = {}
                continue

            # Check alias: model_id key (indent: 4 spaces, e.g. "    gemini-3.7-flash: omp/gemini-3.7-flash-tiered")
            m_match = re.match(r"^    ([a-zA-Z0-9_\-\.\:\+]+):\s*[\"']?([^\"'\s]+)[\"']?", line)
            if m_match and current_backend:
                alias = m_match.group(1).strip()
                target_id = m_match.group(2).strip()
                backends[current_backend][alias] = target_id

        return backends

    @classmethod
    def load_backends(cls) -> Dict[str, Dict[str, str]]:
        """Returns map of {backend: {alias: target_id}}."""
        cfg_path = cls.find_config_path()
        if not cfg_path:
            return {}

        try:
            return cls._simple_yaml_parse(cfg_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    @classmethod
    def resolve_model(cls, backend: str, model_or_alias: str) -> str:
        """
        Resolves a model alias to its canonical target model ID for the given backend.
        If not found in aliases, returns the input unchanged (passthrough).
        """
        norm_backend = backend.lower().strip()
        # Normalize backend alias
        alias_map = {
            "oc": "opencode",
            "cmd": "commandcode",
            "cc": "commandcode",
            "pi": "omp",
            "oh-my-pi": "omp",
            "gw": "gateway",
            "omp-g": "gateway",
            "omp-gateway": "gateway",
            "direct": "gateway",
            "openai": "gateway",
        }
        canonical_backend = alias_map.get(norm_backend, norm_backend)
        all_backends = cls.load_backends()

        backend_models = all_backends.get(canonical_backend, {})
        # Check exact alias match
        if model_or_alias in backend_models:
            return backend_models[model_or_alias]

        # Case-insensitive check
        for alias, target in backend_models.items():
            if alias.lower() == model_or_alias.lower():
                return target

        # Passthrough
        return model_or_alias
