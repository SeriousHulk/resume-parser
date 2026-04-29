from pydantic import BaseModel

from app.config import Settings


class ModelProvider(BaseModel):
    id: str
    label: str
    available: bool
    models: list[str]


class ModelRegistry(BaseModel):
    providers: list[ModelProvider]


def get_model_registry(settings: Settings) -> ModelRegistry:
    cloud_available = bool(settings.cloud_ollama_base_url and settings.cloud_ollama_models)
    gemini_available = settings.has_gemini_key

    return ModelRegistry(
        providers=[
            ModelProvider(
                id="local_ollama",
                label="Local Ollama",
                available=True,
                models=settings.local_ollama_models,
            ),
            ModelProvider(
                id="cloud_ollama",
                label="Cloud Ollama",
                available=cloud_available,
                models=settings.cloud_ollama_models if cloud_available else [],
            ),
            ModelProvider(
                id="gemini",
                label="Gemini",
                available=gemini_available,
                models=settings.gemini_models if gemini_available else [],
            ),
        ]
    )


def validate_provider_model(provider_id: str, model_name: str, settings: Settings) -> bool:
    registry = get_model_registry(settings)
    for provider in registry.providers:
        if provider.id == provider_id:
            return provider.available and model_name in provider.models
    return False
