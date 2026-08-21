"""Real-time LLM Token Pricing Engine integrating `or` CLI and local configs."""

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class ModelPrice:
    input_per_m: float  # Price in USD per 1M tokens
    output_per_m: float # Price in USD per 1M tokens


class PricingEngine:
    """
    Resolves real-time token pricing in USD and IDR:
      1. Local `~/.config/opencode/config.json` cost fields
      2. Dynamic `or models -l` cache
      3. Fallback table / Free tier ($0.0)
    """

    USD_TO_IDR = 16250.0

    _PRICING_CACHE: Dict[str, ModelPrice] = {
        # Defaults / Standard known rates per 1M tokens
        "claude-sonnet": ModelPrice(3.0, 15.0),
        "claude-opus": ModelPrice(5.0, 25.0),
        "claude-haiku": ModelPrice(0.25, 1.25),
        "gemini-3.7-flash": ModelPrice(0.375, 1.875),
        "gemini-3.6-flash": ModelPrice(0.375, 1.875),
        "gemini-3.1-pro": ModelPrice(1.0, 6.0),
        "gemini-2.5-flash": ModelPrice(0.15, 1.25),
        "deepseek-v4-flash": ModelPrice(0.0786, 0.1572),
        "deepseek-v4-pro": ModelPrice(0.66, 1.98),
        "minimax-m3": ModelPrice(0.3, 1.2),
        "kimi-k3": ModelPrice(3.0, 15.0),
        "kimi-k2.7": ModelPrice(0.475, 2.0),
        "hy3": ModelPrice(0.132, 0.528),
    }

    @classmethod
    def get_price(cls, model_id: Optional[str]) -> ModelPrice:
        if not model_id:
            return ModelPrice(0.0, 0.0)

        mid_lower = model_id.lower().strip()

        # Free tier detection
        if ":free" in mid_lower or "-free" in mid_lower or "/free" in mid_lower:
            return ModelPrice(0.0, 0.0)

        # 1. Check opencode config.json
        opencode_cost = cls._lookup_opencode_config(mid_lower)
        if opencode_cost:
            return opencode_cost

        # 2. Check cached/fuzzy lookup in PricingEngine
        for key, price in cls._PRICING_CACHE.items():
            if key in mid_lower:
                return price

        # 3. Dynamic lookup via `or` CLI if available
        or_cost = cls._lookup_or_cli(mid_lower)
        if or_cost:
            return or_cost

        # Default fallback
        return ModelPrice(0.20, 0.80)

    @classmethod
    def _lookup_opencode_config(cls, model_id: str) -> Optional[ModelPrice]:
        config_path = Path.home() / ".config" / "opencode" / "config.json"
        if not config_path.exists():
            return None

        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            providers = data.get("provider", {})
            for _, prov_data in providers.items():
                for model_key, model_info in prov_data.get("models", {}).items():
                    if model_key.lower() in model_id or model_info.get("id", "").lower() in model_id:
                        cost = model_info.get("cost", {})
                        if cost and "input" in cost and "output" in cost:
                            return ModelPrice(float(cost["input"]), float(cost["output"]))
        except Exception:
            pass
        return None

    @classmethod
    def _lookup_or_cli(cls, model_id: str) -> Optional[ModelPrice]:
        or_bin = shutil.which("or")
        if not or_bin:
            return None

        try:
            res = subprocess.run([or_bin, "models", "-l"], capture_output=True, text=True, timeout=5)
            # Find matching line
            for line in res.stdout.splitlines():
                if "|" in line:
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 4:
                        m_name = parts[0].lower()
                        # e.g. "Google: Gemini 3.7 Flash | 1.0M | 0.375 | 1.875"
                        clean_target = model_id.split("/")[-1].replace("-", " ")
                        if clean_target in m_name or any(tok in m_name for tok in model_id.split("/")[-1].split("-") if len(tok) > 3):
                            try:
                                in_p = float(parts[2])
                                out_p = float(parts[3])
                                return ModelPrice(in_p, out_p)
                            except ValueError:
                                pass
        except Exception:
            pass
        return None

    @classmethod
    def calculate_cost(cls, model_id: Optional[str], input_tokens: int, output_tokens: int) -> Tuple[float, float]:
        """Returns (cost_usd, cost_idr)."""
        price = cls.get_price(model_id)
        cost_usd = (input_tokens * price.input_per_m / 1_000_000.0) + (output_tokens * price.output_per_m / 1_000_000.0)
        cost_idr = cost_usd * cls.USD_TO_IDR
        return round(cost_usd, 6), round(cost_idr, 2)
