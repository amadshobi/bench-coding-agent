"""LLM provider registry and helper specs."""

from dataclasses import dataclass
from typing import Dict, List, Optional

from bca.llm.discovery import ModelDiscovery


@dataclass(frozen=True)
class ModelPricing:
    input_per_million: float
    output_per_million: float


@dataclass(frozen=True)
class ModelMetadata:
    model_id: str
    provider: str
    context_window: int
    pricing: ModelPricing


class ModelRegistry:
    """Registry of known AI models, token pricing, context limits, and dynamic discovery."""

    _MODELS: Dict[str, ModelMetadata] = {
        "anthropic/claude-3.7-sonnet": ModelMetadata(
            model_id="anthropic/claude-3.7-sonnet",
            provider="openrouter",
            context_window=200000,
            pricing=ModelPricing(3.0, 15.0),
        ),
        "google/gemini-2.5-flash": ModelMetadata(
            model_id="google/gemini-2.5-flash",
            provider="google_ai",
            context_window=1000000,
            pricing=ModelPricing(0.075, 0.30),
        ),
    }

    @classmethod
    def get_model(cls, model_id: str) -> Optional[ModelMetadata]:
        return cls._MODELS.get(model_id)

    @classmethod
    def list_available_models(cls, backend: Optional[str] = None) -> Dict[str, List[Dict[str, str]]]:
        """Returns auto-discovered models filtered by backend or all."""
        all_models = ModelDiscovery.discover_all()
        if backend:
            normalized = backend.lower().strip()
            if normalized in ("cmd", "commandcode"):
                return {"commandcode": all_models.get("commandcode", [])}
            elif normalized in ("omp", "oh-my-pi"):
                return {"omp": all_models.get("omp", [])}
            elif normalized in ("gateway", "omp-gateway", "direct", "openai"):
                return {"omp-gateway": all_models.get("omp-gateway", [])}
            elif normalized in ("opencode",):
                return {"opencode": all_models.get("opencode", [])}
            return {normalized: all_models.get(normalized, [])}
        return all_models
