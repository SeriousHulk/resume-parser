import os

from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.ollama import OllamaModel

from app.config import Settings
from app.errors import ModelConfigurationError, ResumeExtractionError
from app.model_registry import validate_provider_model
from app.schemas import ResumeData


def markdown_preview(markdown: str, limit: int = 500) -> str:
    return markdown.strip()[:limit]


def build_resume_prompt(markdown: str) -> str:
    return f"""You are an information extraction assistant.

Extract structured resume data from the Markdown below.

Rules:
- The Markdown is the source of truth.
- Do not invent missing information.
- Use null for unknown scalar values.
- Use empty lists for missing repeated sections.
- Preserve dates as written when exact normalization is uncertain.
- Keep descriptions concise.

Resume Markdown:
```markdown
{markdown}
```
"""


def build_agent(provider: str, model: str, settings: Settings) -> Agent:
    if not validate_provider_model(provider, model, settings):
        raise ModelConfigurationError(f"Model '{model}' is not available for provider '{provider}'.")

    if provider == "local_ollama":
        model_instance = OllamaModel(model)
    elif provider == "cloud_ollama":
        # Pydantic AI's Ollama provider uses the OpenAI-compatible API.
        os.environ.setdefault("OLLAMA_BASE_URL", settings.cloud_ollama_base_url)
        if settings.cloud_ollama_api_key:
            os.environ.setdefault("OLLAMA_API_KEY", settings.cloud_ollama_api_key)
        model_instance = OllamaModel(model)
    elif provider == "gemini":
        api_key = settings.gemini_api_key or settings.google_api_key
        if not api_key:
            raise ModelConfigurationError("Gemini is unavailable because no API key is configured.")
        os.environ.setdefault("GOOGLE_API_KEY", api_key)
        model_instance = GoogleModel(model)
    else:
        raise ModelConfigurationError(f"Unknown provider '{provider}'.")

    return Agent(model_instance, output_type=ResumeData)


async def parse_resume_markdown(
    markdown: str,
    provider: str,
    model: str,
    settings: Settings,
) -> ResumeData:
    try:
        agent = build_agent(provider, model, settings)
        result = await agent.run(build_resume_prompt(markdown))
        data = result.output
        data.raw_markdown_preview = markdown_preview(markdown)
        return data
    except ModelConfigurationError:
        raise
    except Exception as exc:
        raise ResumeExtractionError(f"Could not extract resume data: {exc}") from exc
