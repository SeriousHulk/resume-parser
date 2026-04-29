import pytest

from app.config import Settings
from app.parser_agent import build_agent, build_resume_prompt, parse_resume_markdown
from app.schemas import ResumeData


def test_build_resume_prompt_contains_source_markdown() -> None:
    prompt = build_resume_prompt("# Jane Doe\nPython")

    assert "# Jane Doe" in prompt
    assert "Do not invent missing information" in prompt


def test_build_agent_passes_local_ollama_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = {}

    class FakeProvider:
        def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
            seen["base_url"] = base_url
            seen["api_key"] = api_key

    class FakeOllamaModel:
        def __init__(self, model_name: str, *, provider: FakeProvider) -> None:
            seen["model_instance"] = self
            seen["model_name"] = model_name
            seen["provider"] = provider

    monkeypatch.setattr("app.parser_agent.OllamaProvider", FakeProvider)
    monkeypatch.setattr("app.parser_agent.OllamaModel", FakeOllamaModel)
    monkeypatch.setattr(
        "app.parser_agent.Agent",
        lambda model_instance, output_type: model_instance,
    )

    result = build_agent(
        "local_ollama",
        "qwen3.5:0.8b-q8_0",
        Settings(
            local_ollama_base_url="http://localhost:11434",
            local_ollama_models=["qwen3.5:0.8b-q8_0"],
            _env_file=None,
        ),
    )

    assert result is seen["model_instance"]
    assert isinstance(seen["provider"], FakeProvider)
    assert seen["model_name"] == "qwen3.5:0.8b-q8_0"
    assert seen["base_url"] == "http://localhost:11434"
    assert seen["api_key"] is None


def test_build_agent_passes_cloud_ollama_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = {}

    class FakeProvider:
        def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
            seen["base_url"] = base_url
            seen["api_key"] = api_key

    class FakeOllamaModel:
        def __init__(self, model_name: str, *, provider: FakeProvider) -> None:
            seen["model_name"] = model_name
            seen["provider"] = provider

    monkeypatch.setattr("app.parser_agent.OllamaProvider", FakeProvider)
    monkeypatch.setattr("app.parser_agent.OllamaModel", FakeOllamaModel)
    monkeypatch.setattr(
        "app.parser_agent.Agent",
        lambda model_instance, output_type: model_instance,
    )

    build_agent(
        "cloud_ollama",
        "cloud-model",
        Settings(
            cloud_ollama_base_url="https://ollama.example.com",
            cloud_ollama_api_key="secret",
            cloud_ollama_models=["cloud-model"],
            _env_file=None,
        ),
    )

    assert seen["model_name"] == "cloud-model"
    assert seen["base_url"] == "https://ollama.example.com"
    assert seen["api_key"] == "secret"


@pytest.mark.asyncio
async def test_parse_resume_markdown_returns_resume_data(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResult:
        output = ResumeData(skills=["Python"], raw_markdown_preview="# Jane Doe")

    class FakeAgent:
        async def run(self, prompt: str) -> FakeResult:
            assert "Jane Doe" in prompt
            return FakeResult()

    monkeypatch.setattr(
        "app.parser_agent.build_agent",
        lambda provider, model, settings: FakeAgent(),
    )

    result = await parse_resume_markdown(
        markdown="# Jane Doe\nPython",
        provider="local_ollama",
        model="llama3.2",
        settings=Settings(),
    )

    assert result.skills == ["Python"]
    assert result.raw_markdown_preview == "# Jane Doe\nPython"


def test_raw_markdown_preview_is_truncated() -> None:
    from app.parser_agent import markdown_preview

    assert markdown_preview("a" * 600, limit=20) == "a" * 20
