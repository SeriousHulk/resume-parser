from app.config import Settings
from app.model_registry import get_model_registry, validate_provider_model


def test_local_ollama_is_available_by_default() -> None:
    settings = Settings()

    registry = get_model_registry(settings)

    local = next(provider for provider in registry.providers if provider.id == "local_ollama")
    assert local.available is True
    assert local.models == ["llama3.2", "qwen3"]


def test_gemini_is_unavailable_without_api_key() -> None:
    settings = Settings(gemini_api_key="", google_api_key="")

    registry = get_model_registry(settings)

    gemini = next(provider for provider in registry.providers if provider.id == "gemini")
    assert gemini.available is False
    assert gemini.models == []


def test_gemini_is_available_with_either_api_key() -> None:
    settings = Settings(gemini_api_key="secret", google_api_key="")

    registry = get_model_registry(settings)

    gemini = next(provider for provider in registry.providers if provider.id == "gemini")
    assert gemini.available is True
    assert gemini.models == ["gemini-2.5-flash"]


def test_cloud_ollama_requires_base_url_and_models() -> None:
    settings = Settings(cloud_ollama_base_url="", cloud_ollama_models=[])

    registry = get_model_registry(settings)

    cloud = next(provider for provider in registry.providers if provider.id == "cloud_ollama")
    assert cloud.available is False
    assert cloud.models == []


def test_validate_provider_model_rejects_disabled_provider() -> None:
    settings = Settings(gemini_api_key="", google_api_key="")

    assert validate_provider_model("gemini", "gemini-2.5-flash", settings) is False


def test_validate_provider_model_accepts_available_model() -> None:
    settings = Settings()

    assert validate_provider_model("local_ollama", "llama3.2", settings) is True
