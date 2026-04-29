import pytest

from app.config import Settings
from app.parser_agent import build_resume_prompt, parse_resume_markdown
from app.schemas import ResumeData


def test_build_resume_prompt_contains_source_markdown() -> None:
    prompt = build_resume_prompt("# Jane Doe\nPython")

    assert "# Jane Doe" in prompt
    assert "Do not invent missing information" in prompt


@pytest.mark.asyncio
async def test_parse_resume_markdown_returns_resume_data(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResult:
        output = ResumeData(skills=["Python"], raw_markdown_preview="# Jane Doe")

    class FakeAgent:
        async def run(self, prompt: str) -> FakeResult:
            assert "Jane Doe" in prompt
            return FakeResult()

    monkeypatch.setattr("app.parser_agent.build_agent", lambda provider, model, settings: FakeAgent())

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
