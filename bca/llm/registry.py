"""LLM provider registry and helper specs."""

from dataclasses import dataclass
from typing import Dict, Optional


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
    """Registry of known AI models, token pricing, and context limits."""

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
