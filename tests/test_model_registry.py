import pytest

from app.config import Settings
from app.model_registry import get_model_registry, validate_provider_model


def test_local_ollama_is_available_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OLLAMA_MODELS", raising=False)
    monkeypatch.delenv("LOCAL_OLLAMA_MODELS", raising=False)
    monkeypatch.delenv("CLOUD_OLLAMA_MODELS", raising=False)

    settings = Settings(_env_file=None)

    registry = get_model_registry(settings)

    local = next(provider for provider in registry.providers if provider.id == "local_ollama")
    assert local.available is True
    assert local.models == ["qwen3.5:0.8b-q8_0"]


def test_model_lists_accept_comma_separated_env_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_OLLAMA_MODELS", "qwen3.5:0.8b-q8_0,llama3.2")
    monkeypatch.setenv("CLOUD_OLLAMA_BASE_URL", "https://ollama.example.com")
    monkeypatch.setenv("CLOUD_OLLAMA_MODELS", "cloud-a, cloud-b")
    monkeypatch.setenv("GEMINI_API_KEY", "secret")
    monkeypatch.setenv("GEMINI_MODELS", "gemini-2.5-flash,gemini-2.5-pro")

    settings = Settings(_env_file=None)

    assert settings.local_ollama_models == ["qwen3.5:0.8b-q8_0", "llama3.2"]
    assert settings.cloud_ollama_models == ["cloud-a", "cloud-b"]
    assert settings.gemini_models == ["gemini-2.5-flash", "gemini-2.5-pro"]


def test_model_lists_accept_json_env_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_OLLAMA_MODELS", '["qwen3.5:0.8b-q8_0","ministral-3:3b"]')
    monkeypatch.setenv("CLOUD_OLLAMA_MODELS", '["gpt-oss:20b-cloud","gemma4:31b-cloud"]')

    settings = Settings(_env_file=None)

    assert settings.local_ollama_models == ["qwen3.5:0.8b-q8_0", "ministral-3:3b"]
    assert settings.cloud_ollama_models == ["gpt-oss:20b-cloud", "gemma4:31b-cloud"]


def test_shared_ollama_models_feed_local_and_cloud_when_specific_values_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OLLAMA_MODELS", '["gpt-oss:20b-cloud","gemma4:31b-cloud"]')
    monkeypatch.delenv("LOCAL_OLLAMA_MODELS", raising=False)
    monkeypatch.delenv("CLOUD_OLLAMA_MODELS", raising=False)

    settings = Settings(_env_file=None)

    assert settings.local_ollama_models == ["gpt-oss:20b-cloud", "gemma4:31b-cloud"]
    assert settings.cloud_ollama_models == ["gpt-oss:20b-cloud", "gemma4:31b-cloud"]


def test_shared_ollama_models_feed_blank_provider_specific_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OLLAMA_MODELS", '["gpt-oss:20b-cloud","gemma4:31b-cloud"]')
    monkeypatch.setenv("LOCAL_OLLAMA_MODELS", "")
    monkeypatch.setenv("CLOUD_OLLAMA_MODELS", "")

    settings = Settings(_env_file=None)

    assert settings.local_ollama_models == ["gpt-oss:20b-cloud", "gemma4:31b-cloud"]
    assert settings.cloud_ollama_models == ["gpt-oss:20b-cloud", "gemma4:31b-cloud"]


def test_gemini_is_unavailable_without_api_key() -> None:
    settings = Settings(gemini_api_key="", google_api_key="", _env_file=None)

    registry = get_model_registry(settings)

    gemini = next(provider for provider in registry.providers if provider.id == "gemini")
    assert gemini.available is False
    assert gemini.models == []


def test_gemini_is_available_with_either_api_key() -> None:
    settings = Settings(gemini_api_key="secret", google_api_key="", _env_file=None)

    registry = get_model_registry(settings)

    gemini = next(provider for provider in registry.providers if provider.id == "gemini")
    assert gemini.available is True
    assert gemini.models == ["gemini-2.5-flash"]


def test_cloud_ollama_requires_base_url_and_models() -> None:
    settings = Settings(cloud_ollama_base_url="", cloud_ollama_models=[], _env_file=None)

    registry = get_model_registry(settings)

    cloud = next(provider for provider in registry.providers if provider.id == "cloud_ollama")
    assert cloud.available is False
    assert cloud.models == []


def test_validate_provider_model_rejects_disabled_provider() -> None:
    settings = Settings(gemini_api_key="", google_api_key="", _env_file=None)

    assert validate_provider_model("gemini", "gemini-2.5-flash", settings) is False


def test_validate_provider_model_accepts_available_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OLLAMA_MODELS", raising=False)
    monkeypatch.delenv("LOCAL_OLLAMA_MODELS", raising=False)
    monkeypatch.delenv("CLOUD_OLLAMA_MODELS", raising=False)

    settings = Settings(_env_file=None)

    assert validate_provider_model("local_ollama", "qwen3.5:0.8b-q8_0", settings) is True
