# Resume Parser Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a limited-scope FastAPI resume parser with drag-and-drop upload, MarkItDown document conversion, targeted Tesseract OCR, Pydantic AI extraction, provider/model switching, and validated JSON output.

**Architecture:** The app is a small FastAPI service that serves a plain HTML/CSS/JavaScript UI and exposes JSON API endpoints. Uploaded files are validated, converted to Markdown with MarkItDown, optionally supplemented with Tesseract OCR text, then parsed by a Pydantic AI agent into strict Pydantic schemas. Provider selection is configuration-driven for local Ollama, cloud Ollama-compatible endpoints, and Gemini when an API key is present.

**Tech Stack:** Python 3.12, FastAPI, Jinja2, Pydantic Settings, Pydantic AI, MarkItDown, pytesseract, Pillow, pytest, httpx, plain HTML/CSS/JavaScript.

---

## Documentation Sources

Context7 MCP was requested, but no Context7 tools were available in this Codex session after tool discovery. Use these current official sources while implementing:

- Pydantic AI structured output: `https://pydantic.dev/docs/ai/core-concepts/output/`
- Pydantic AI Ollama model: `https://pydantic.dev/docs/ai/api/models/ollama/`
- Pydantic AI Google/Gemini model: `https://pydantic.dev/docs/ai/models/google`
- MarkItDown GitHub README: `https://github.com/microsoft/markitdown`
- MarkItDown OCR plugin README for comparison only: `https://github.com/microsoft/markitdown/blob/main/packages/markitdown-ocr/README.md`
- pytesseract project docs: `https://pypi.org/project/pytesseract/`

Important implementation notes from current docs:

- Pydantic AI defaults to tool-based structured output, which is the most portable mode across providers.
- `OllamaModel` uses Ollama's OpenAI-compatible chat completions API.
- Current Pydantic AI docs warn that Ollama Cloud can accept JSON schema settings without enforcing them, so use default tool output rather than native output for cloud Ollama.
- `GoogleModel` supports Gemini through the Generative Language API when `GOOGLE_API_KEY` is configured.
- MarkItDown's Python API exposes `MarkItDown().convert(path).text_content`.
- MarkItDown `convert_stream()` now requires a binary file-like object.
- MarkItDown's optional OCR plugin uses LLM vision; this project uses Tesseract instead.

## File Map

Create these files:

- `pyproject.toml`: project metadata, runtime dependencies, dev dependencies, pytest configuration.
- `.env.example`: safe default configuration.
- `README.md`: setup, Tesseract note, run instructions, test instructions.
- `app/__init__.py`: package marker.
- `app/config.py`: environment settings and computed provider availability.
- `app/errors.py`: small app-specific exception types.
- `app/schemas.py`: Pydantic request/response and resume extraction schemas.
- `app/model_registry.py`: provider/model availability logic.
- `app/document_converter.py`: upload validation and MarkItDown conversion.
- `app/ocr.py`: Tesseract trigger detection and OCR append logic.
- `app/parser_agent.py`: Pydantic AI model construction and resume parsing agent.
- `app/main.py`: FastAPI app, HTML route, API routes.
- `app/templates/index.html`: simple UI shell.
- `app/static/styles.css`: restrained UI styling with drag/drop states.
- `app/static/app.js`: model loading, drag/drop, parse request, JSON rendering.
- `tests/conftest.py`: reusable test app and fixtures.
- `tests/test_schemas.py`: schema defaults and validation.
- `tests/test_model_registry.py`: provider availability behavior.
- `tests/test_document_converter.py`: file validation and conversion behavior.
- `tests/test_ocr.py`: OCR trigger and append behavior.
- `tests/test_parser_agent.py`: mocked parser behavior.
- `tests/test_api.py`: API endpoint behavior.

Do not create a database, auth layer, job queue, frontend framework, batch parser, or resume scoring system.

## Task 1: Project Skeleton and Dependencies

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `README.md`
- Create: `app/__init__.py`
- Create: `tests/conftest.py`

- [x] **Step 1: Create project metadata and dependencies**

Create `pyproject.toml`:

```toml
[project]
name = "resume-parser"
version = "0.1.0"
description = "FastAPI resume parser using MarkItDown, Tesseract OCR, and Pydantic AI."
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "jinja2>=3.1.4",
    "markitdown[pdf,docx]>=0.1.5",
    "pillow>=10.4.0",
    "pydantic>=2.9.0",
    "pydantic-ai>=1.0.0",
    "pydantic-settings>=2.6.0",
    "python-multipart>=0.0.12",
    "pytesseract>=0.3.13",
    "uvicorn[standard]>=0.32.0",
]

[dependency-groups]
dev = [
    "httpx>=0.27.2",
    "pytest>=8.3.3",
    "pytest-asyncio>=0.24.0",
    "ruff>=0.7.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
```

- [x] **Step 2: Create safe environment example**

Create `.env.example`:

```text
APP_NAME=Resume Parser
MAX_UPLOAD_MB=10
ENABLE_OCR=true
TESSERACT_CMD=
OCR_MIN_MARKDOWN_CHARS=200

LOCAL_OLLAMA_BASE_URL=http://localhost:11434
LOCAL_OLLAMA_MODELS=qwen3.5:0.8b-q8_0

CLOUD_OLLAMA_BASE_URL=
CLOUD_OLLAMA_API_KEY=
CLOUD_OLLAMA_MODELS=

GEMINI_API_KEY=
GOOGLE_API_KEY=
GEMINI_MODELS=gemini-2.5-flash
```

- [x] **Step 3: Create README**

Create `README.md`:

```markdown
# Resume Parser

A small FastAPI resume parser with a plain HTML UI, MarkItDown document conversion, targeted Tesseract OCR, and Pydantic AI structured extraction.

## Features

- Drag-and-drop resume upload with file picker fallback
- PDF, DOCX, and best-effort DOC conversion through MarkItDown
- Targeted Tesseract OCR pass for image-only or embedded-image content
- Local Ollama, cloud Ollama-compatible, and Gemini provider options
- Pydantic-validated JSON output

## Setup

```powershell
uv sync
Copy-Item .env.example .env
```

Tesseract OCR must be installed separately. Either put the `tesseract` executable on `PATH` or set `TESSERACT_CMD` in `.env`.

## Run

```powershell
uv run uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Test

```powershell
uv run pytest -v
```
```

- [x] **Step 4: Create package and test fixture scaffolding**

Create `app/__init__.py`:

```python
"""Resume parser application package."""
```

Create `tests/conftest.py`:

```python
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def tmp_resume_file(tmp_path: Path) -> Path:
    path = tmp_path / "resume.pdf"
    path.write_bytes(b"%PDF-1.4 fake test file")
    return path


@pytest.fixture
def client() -> Iterator[TestClient]:
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
```

- [x] **Step 5: Run initial test command**

Run:

```powershell
uv run pytest -v
```

Expected: collection fails because `app.main` does not exist yet. This is acceptable for the skeleton checkpoint.

- [x] **Step 6: Commit**

Run:

```powershell
git add pyproject.toml .env.example README.md app/__init__.py tests/conftest.py
git commit -m "chore: add project skeleton"
```

## Task 2: Configuration and Model Registry

**Files:**
- Create: `app/config.py`
- Create: `app/model_registry.py`
- Create: `tests/test_model_registry.py`

- [x] **Step 1: Write model registry tests**

Create `tests/test_model_registry.py`:

```python
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
```

- [x] **Step 2: Run tests to verify failure**

Run:

```powershell
uv run pytest tests/test_model_registry.py -v
```

Expected: FAIL because `app.config` and `app.model_registry` do not exist.

- [x] **Step 3: Implement settings**

Create `app/config.py`:

```python
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Resume Parser"
    max_upload_mb: int = 10

    enable_ocr: bool = True
    tesseract_cmd: str = ""
    ocr_min_markdown_chars: int = 200

    local_ollama_base_url: str = "http://localhost:11434"
    local_ollama_models: list[str] = Field(default_factory=lambda: ["llama3.2", "qwen3"])

    cloud_ollama_base_url: str = ""
    cloud_ollama_api_key: str = ""
    cloud_ollama_models: list[str] = Field(default_factory=list)

    gemini_api_key: str = ""
    google_api_key: str = ""
    gemini_models: list[str] = Field(default_factory=lambda: ["gemini-2.5-flash"])

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def has_gemini_key(self) -> bool:
        return bool(self.gemini_api_key or self.google_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [x] **Step 4: Implement registry**

Create `app/model_registry.py`:

```python
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
```

- [x] **Step 5: Run registry tests**

Run:

```powershell
uv run pytest tests/test_model_registry.py -v
```

Expected: PASS.

- [x] **Step 6: Commit**

Run:

```powershell
git add app/config.py app/model_registry.py tests/test_model_registry.py
git commit -m "feat: add provider model registry"
```

## Task 3: Resume Schemas

**Files:**
- Create: `app/schemas.py`
- Create: `tests/test_schemas.py`

- [x] **Step 1: Write schema tests**

Create `tests/test_schemas.py`:

```python
from app.schemas import ResumeData


def test_resume_data_defaults_to_empty_sections() -> None:
    resume = ResumeData()

    assert resume.contact.name is None
    assert resume.education == []
    assert resume.work_experience == []
    assert resume.skills == []
    assert resume.certifications == []
    assert resume.projects == []
    assert resume.languages == []
    assert resume.raw_markdown_preview == ""


def test_resume_data_accepts_expected_fields() -> None:
    resume = ResumeData.model_validate(
        {
            "contact": {
                "name": "Jane Doe",
                "email": "jane@example.com",
                "phone": "+1 555 123 4567",
                "location": "New York, NY",
                "links": ["https://linkedin.com/in/janedoe"],
            },
            "summary": "Backend engineer.",
            "education": [
                {
                    "institution": "Example University",
                    "degree": "BS",
                    "field_of_study": "Computer Science",
                    "graduation_year": "2020",
                }
            ],
            "work_experience": [
                {
                    "company": "Acme",
                    "position": "Engineer",
                    "description": "Built APIs.",
                    "highlights": ["FastAPI", "Postgres"],
                }
            ],
            "skills": ["Python", "FastAPI"],
            "raw_markdown_preview": "Jane Doe",
        }
    )

    assert resume.contact.email == "jane@example.com"
    assert resume.education[0].institution == "Example University"
    assert resume.work_experience[0].highlights == ["FastAPI", "Postgres"]
```

- [x] **Step 2: Run schema tests to verify failure**

Run:

```powershell
uv run pytest tests/test_schemas.py -v
```

Expected: FAIL because `app.schemas` does not exist.

- [x] **Step 3: Implement schemas**

Create `app/schemas.py`:

```python
from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    links: list[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    graduation_year: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class WorkExperienceItem(BaseModel):
    company: str | None = None
    position: str | None = None
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    duration: str | None = None
    description: str | None = None
    highlights: list[str] = Field(default_factory=list)


class CertificationItem(BaseModel):
    name: str | None = None
    issuer: str | None = None
    year: str | None = None


class ProjectItem(BaseModel):
    name: str | None = None
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)


class ResumeData(BaseModel):
    contact: ContactInfo = Field(default_factory=ContactInfo)
    summary: str | None = None
    education: list[EducationItem] = Field(default_factory=list)
    work_experience: list[WorkExperienceItem] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    certifications: list[CertificationItem] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    raw_markdown_preview: str = ""


class ParseResponse(BaseModel):
    provider: str
    model: str
    filename: str
    data: ResumeData
```

- [x] **Step 4: Run schema tests**

Run:

```powershell
uv run pytest tests/test_schemas.py -v
```

Expected: PASS.

- [x] **Step 5: Commit**

Run:

```powershell
git add app/schemas.py tests/test_schemas.py
git commit -m "feat: add resume schemas"
```

## Task 4: App Errors

**Files:**
- Create: `app/errors.py`

- [ ] **Step 1: Create app-specific exceptions**

Create `app/errors.py`:

```python
class ResumeParserError(Exception):
    """Base class for expected resume parser failures."""


class FileValidationError(ResumeParserError):
    """Raised when an uploaded file is missing, too large, or unsupported."""


class DocumentConversionError(ResumeParserError):
    """Raised when MarkItDown cannot produce usable Markdown."""


class OcrConfigurationError(ResumeParserError):
    """Raised when OCR is required but Tesseract is not configured."""


class OcrProcessingError(ResumeParserError):
    """Raised when OCR runs but produces no usable text."""


class ModelConfigurationError(ResumeParserError):
    """Raised when a requested provider or model is unavailable."""


class ResumeExtractionError(ResumeParserError):
    """Raised when the model response cannot be converted to ResumeData."""
```

- [ ] **Step 2: Run existing tests**

Run:

```powershell
uv run pytest tests/test_schemas.py tests/test_model_registry.py -v
```

Expected: PASS.

- [ ] **Step 3: Commit**

Run:

```powershell
git add app/errors.py
git commit -m "chore: add app error types"
```

## Task 5: MarkItDown Document Converter

**Files:**
- Create: `app/document_converter.py`
- Create: `tests/test_document_converter.py`

- [ ] **Step 1: Write converter tests**

Create `tests/test_document_converter.py`:

```python
from pathlib import Path

import pytest

from app.config import Settings
from app.document_converter import (
    ALLOWED_EXTENSIONS,
    ConvertedDocument,
    convert_resume_file,
    validate_upload_metadata,
)
from app.errors import DocumentConversionError, FileValidationError


def test_allowed_extensions_match_spec() -> None:
    assert ALLOWED_EXTENSIONS == {".pdf", ".docx", ".doc"}


def test_validate_upload_metadata_accepts_supported_extension() -> None:
    settings = Settings(max_upload_mb=1)

    validate_upload_metadata("resume.pdf", 100, settings)


def test_validate_upload_metadata_rejects_unsupported_extension() -> None:
    settings = Settings(max_upload_mb=1)

    with pytest.raises(FileValidationError, match="Unsupported file type"):
        validate_upload_metadata("resume.txt", 100, settings)


def test_validate_upload_metadata_rejects_large_file() -> None:
    settings = Settings(max_upload_mb=1)

    with pytest.raises(FileValidationError, match="File is too large"):
        validate_upload_metadata("resume.pdf", 2 * 1024 * 1024, settings)


def test_convert_resume_file_returns_markdown(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    path = tmp_path / "resume.pdf"
    path.write_bytes(b"fake")

    class FakeResult:
        text_content = "# Jane Doe\nPython developer"

    class FakeMarkItDown:
        def convert(self, file_path: str) -> FakeResult:
            assert file_path == str(path)
            return FakeResult()

    monkeypatch.setattr("app.document_converter.MarkItDown", FakeMarkItDown)

    result = convert_resume_file(path)

    assert isinstance(result, ConvertedDocument)
    assert result.markdown == "# Jane Doe\nPython developer"
    assert result.markdown_char_count == len("# Jane Doe\nPython developer")


def test_convert_resume_file_rejects_empty_markdown(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "resume.pdf"
    path.write_bytes(b"fake")

    class FakeResult:
        text_content = "   "

    class FakeMarkItDown:
        def convert(self, file_path: str) -> FakeResult:
            return FakeResult()

    monkeypatch.setattr("app.document_converter.MarkItDown", FakeMarkItDown)

    with pytest.raises(DocumentConversionError, match="No readable Markdown"):
        convert_resume_file(path)
```

- [ ] **Step 2: Run converter tests to verify failure**

Run:

```powershell
uv run pytest tests/test_document_converter.py -v
```

Expected: FAIL because `app.document_converter` does not exist.

- [ ] **Step 3: Implement converter**

Create `app/document_converter.py`:

```python
from pathlib import Path

from markitdown import MarkItDown
from pydantic import BaseModel

from app.config import Settings
from app.errors import DocumentConversionError, FileValidationError

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}


class ConvertedDocument(BaseModel):
    markdown: str
    markdown_char_count: int


def validate_upload_metadata(filename: str, size_bytes: int, settings: Settings) -> None:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise FileValidationError("Unsupported file type. Please upload a PDF, DOCX, or DOC file.")
    if size_bytes > settings.max_upload_bytes:
        raise FileValidationError(f"File is too large. Maximum size is {settings.max_upload_mb} MB.")


def convert_resume_file(path: Path) -> ConvertedDocument:
    try:
        result = MarkItDown(enable_plugins=False).convert(str(path))
    except Exception as exc:
        raise DocumentConversionError(f"Could not convert document with MarkItDown: {exc}") from exc

    markdown = (result.text_content or "").strip()
    if not markdown:
        raise DocumentConversionError("No readable Markdown was produced from the uploaded document.")

    return ConvertedDocument(markdown=markdown, markdown_char_count=len(markdown))
```

- [ ] **Step 4: Run converter tests**

Run:

```powershell
uv run pytest tests/test_document_converter.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```powershell
git add app/document_converter.py tests/test_document_converter.py
git commit -m "feat: add markitdown document conversion"
```

## Task 6: Tesseract OCR Trigger and Append Logic

**Files:**
- Create: `app/ocr.py`
- Create: `tests/test_ocr.py`

- [ ] **Step 1: Write OCR tests**

Create `tests/test_ocr.py`:

```python
from pathlib import Path

import pytest

from app.config import Settings
from app.errors import OcrConfigurationError
from app.ocr import OcrResult, append_ocr_text, should_run_ocr


def test_should_run_ocr_false_when_disabled(tmp_path: Path) -> None:
    settings = Settings(enable_ocr=False)

    assert should_run_ocr(tmp_path / "resume.pdf", "", settings) is False


def test_should_run_ocr_true_for_short_markdown_pdf(tmp_path: Path) -> None:
    settings = Settings(enable_ocr=True, ocr_min_markdown_chars=200)

    assert should_run_ocr(tmp_path / "resume.pdf", "tiny", settings) is True


def test_should_run_ocr_true_for_image_placeholder(tmp_path: Path) -> None:
    settings = Settings(enable_ocr=True, ocr_min_markdown_chars=10)

    assert should_run_ocr(tmp_path / "resume.docx", "![image](media/image1.png)", settings) is True


def test_should_run_ocr_false_for_enough_markdown_without_image(tmp_path: Path) -> None:
    settings = Settings(enable_ocr=True, ocr_min_markdown_chars=10)

    assert should_run_ocr(tmp_path / "resume.pdf", "Jane Doe\nPython Developer", settings) is False


def test_append_ocr_text_appends_labeled_section() -> None:
    result = append_ocr_text("# Jane Doe", OcrResult(text="OCR phone number", attempted=True))

    assert result == "# Jane Doe\n\n## OCR Extracted Text\n\nOCR phone number"


def test_append_ocr_text_leaves_markdown_when_no_ocr_text() -> None:
    result = append_ocr_text("# Jane Doe", OcrResult(text="", attempted=True))

    assert result == "# Jane Doe"


def test_tesseract_config_error_when_required_but_unavailable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from app.ocr import run_tesseract_ocr

    monkeypatch.setattr("app.ocr.shutil.which", lambda command: None)

    with pytest.raises(OcrConfigurationError, match="Tesseract OCR is not configured"):
        run_tesseract_ocr(tmp_path / "resume.pdf", Settings(tesseract_cmd=""))
```

- [ ] **Step 2: Run OCR tests to verify failure**

Run:

```powershell
uv run pytest tests/test_ocr.py -v
```

Expected: FAIL because `app.ocr` does not exist.

- [ ] **Step 3: Implement OCR module**

Create `app/ocr.py`:

```python
from pathlib import Path
import shutil

import pytesseract
from pydantic import BaseModel

from app.config import Settings
from app.errors import OcrConfigurationError


class OcrResult(BaseModel):
    text: str = ""
    attempted: bool = False


def should_run_ocr(path: Path, markdown: str, settings: Settings) -> bool:
    if not settings.enable_ocr:
        return False

    normalized = markdown.strip()
    lower = normalized.lower()
    suffix = path.suffix.lower()

    if len(normalized) < settings.ocr_min_markdown_chars and suffix in {".pdf", ".docx", ".doc"}:
        return True
    return any(marker in lower for marker in ("![", "<img", "image:"))


def ensure_tesseract_available(settings: Settings) -> str:
    configured = settings.tesseract_cmd.strip()
    if configured:
        pytesseract.pytesseract.tesseract_cmd = configured
        return configured

    discovered = shutil.which("tesseract")
    if discovered:
        return discovered

    raise OcrConfigurationError(
        "Tesseract OCR is not configured. Install Tesseract or set TESSERACT_CMD."
    )


def run_tesseract_ocr(path: Path, settings: Settings) -> OcrResult:
    ensure_tesseract_available(settings)

    # First implementation is intentionally conservative. Full PDF page rendering and DOCX
    # image extraction can extend this function while keeping the same public contract.
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}:
        text = pytesseract.image_to_string(str(path)).strip()
        return OcrResult(text=text, attempted=True)

    return OcrResult(text="", attempted=True)


def append_ocr_text(markdown: str, ocr_result: OcrResult) -> str:
    if not ocr_result.text.strip():
        return markdown
    return f"{markdown.rstrip()}\n\n## OCR Extracted Text\n\n{ocr_result.text.strip()}"
```

- [ ] **Step 4: Run OCR tests**

Run:

```powershell
uv run pytest tests/test_ocr.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```powershell
git add app/ocr.py tests/test_ocr.py
git commit -m "feat: add tesseract ocr hooks"
```

## Task 7: Pydantic AI Parser Agent

**Files:**
- Create: `app/parser_agent.py`
- Create: `tests/test_parser_agent.py`

- [ ] **Step 1: Write parser tests with mocked agent**

Create `tests/test_parser_agent.py`:

```python
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
    assert result.raw_markdown_preview == "# Jane Doe"


def test_raw_markdown_preview_is_truncated() -> None:
    from app.parser_agent import markdown_preview

    assert markdown_preview("a" * 600, limit=20) == "a" * 20
```

- [ ] **Step 2: Run parser tests to verify failure**

Run:

```powershell
uv run pytest tests/test_parser_agent.py -v
```

Expected: FAIL because `app.parser_agent` does not exist.

- [ ] **Step 3: Implement parser agent**

Create `app/parser_agent.py`:

```python
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
        # Pydantic AI's Ollama provider uses the OpenAI-compatible API. Cloud-specific
        # authentication is kept environment-driven so hosted endpoints can vary.
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
```

- [ ] **Step 4: Run parser tests**

Run:

```powershell
uv run pytest tests/test_parser_agent.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```powershell
git add app/parser_agent.py tests/test_parser_agent.py
git commit -m "feat: add pydantic ai parser agent"
```

## Task 8: FastAPI Routes and Upload Flow

**Files:**
- Create: `app/main.py`
- Create: `tests/test_api.py`

- [ ] **Step 1: Write API tests**

Create `tests/test_api.py`:

```python
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.schemas import ResumeData


def test_index_loads(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Resume Parser" in response.text


def test_models_endpoint_returns_providers(client: TestClient) -> None:
    response = client.get("/api/models")

    assert response.status_code == 200
    payload = response.json()
    assert payload["providers"][0]["id"] == "local_ollama"


def test_parse_rejects_unsupported_file(client: TestClient) -> None:
    response = client.post(
        "/api/parse",
        data={"provider": "local_ollama", "model": "llama3.2"},
        files={"file": ("resume.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_parse_returns_resume_data(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
    tmp_path: Path,
) -> None:
    async def fake_parse_resume_markdown(markdown: str, provider: str, model: str, settings):
        assert provider == "local_ollama"
        assert model == "llama3.2"
        return ResumeData(skills=["Python"], raw_markdown_preview=markdown[:500])

    monkeypatch.setattr("app.main.convert_resume_file", lambda path: type("Doc", (), {"markdown": "# Jane"})())
    monkeypatch.setattr("app.main.should_run_ocr", lambda path, markdown, settings: False)
    monkeypatch.setattr("app.main.parse_resume_markdown", fake_parse_resume_markdown)

    response = client.post(
        "/api/parse",
        data={"provider": "local_ollama", "model": "llama3.2"},
        files={"file": ("resume.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "local_ollama"
    assert payload["data"]["skills"] == ["Python"]
```

- [ ] **Step 2: Run API tests to verify failure**

Run:

```powershell
uv run pytest tests/test_api.py -v
```

Expected: FAIL because `app.main` does not exist.

- [ ] **Step 3: Implement FastAPI app**

Create `app/main.py`:

```python
from pathlib import Path
import tempfile

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import Settings, get_settings
from app.document_converter import convert_resume_file, validate_upload_metadata
from app.errors import ResumeParserError
from app.model_registry import get_model_registry, validate_provider_model
from app.ocr import append_ocr_text, run_tesseract_ocr, should_run_ocr
from app.parser_agent import parse_resume_markdown
from app.schemas import ParseResponse

app = FastAPI(title="Resume Parser")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/models")
async def models(settings: Settings = Depends(get_settings)):
    return get_model_registry(settings)


@app.post("/api/parse", response_model=ParseResponse)
async def parse_resume(
    file: UploadFile = File(...),
    provider: str = Form(...),
    model: str = Form(...),
    settings: Settings = Depends(get_settings),
) -> ParseResponse:
    content = await file.read()
    try:
        validate_upload_metadata(file.filename or "", len(content), settings)
        if not validate_provider_model(provider, model, settings):
            raise HTTPException(status_code=400, detail="Selected provider or model is unavailable.")

        suffix = Path(file.filename or "resume").suffix.lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            converted = convert_resume_file(tmp_path)
            markdown = converted.markdown
            if should_run_ocr(tmp_path, markdown, settings):
                ocr_result = run_tesseract_ocr(tmp_path, settings)
                markdown = append_ocr_text(markdown, ocr_result)

            data = await parse_resume_markdown(markdown, provider, model, settings)
            return ParseResponse(provider=provider, model=model, filename=file.filename or "", data=data)
        finally:
            tmp_path.unlink(missing_ok=True)
    except HTTPException:
        raise
    except ResumeParserError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
```

- [ ] **Step 4: Run API tests**

Run:

```powershell
uv run pytest tests/test_api.py -v
```

Expected: PASS after UI template/static files are created in the next task. If this fails because template/static directories are missing, continue to Task 9 before rerunning.

- [ ] **Step 5: Commit after Task 9 completes**

Do not commit `app/main.py` alone if tests fail due to missing UI files. Commit it with Task 9.

## Task 9: Simple HTML UI with Drag-and-Drop

**Files:**
- Create: `app/templates/index.html`
- Create: `app/static/styles.css`
- Create: `app/static/app.js`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Create HTML template**

Create `app/templates/index.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Resume Parser</title>
    <link rel="stylesheet" href="/static/styles.css" />
  </head>
  <body>
    <main class="shell">
      <section class="workspace" aria-labelledby="page-title">
        <div class="controls">
          <h1 id="page-title">Resume Parser</h1>

          <label id="drop-zone" class="drop-zone" for="file-input">
            <span class="drop-title">Drop resume here</span>
            <span id="file-name" class="drop-meta">PDF, DOCX, or DOC</span>
            <input id="file-input" type="file" accept=".pdf,.docx,.doc" />
          </label>

          <label>
            Provider
            <select id="provider-select"></select>
          </label>

          <label>
            Model
            <select id="model-select"></select>
          </label>

          <button id="parse-button" type="button">Parse Resume</button>
          <p id="status" role="status"></p>
        </div>

        <div class="output">
          <div class="output-header">
            <h2>Extracted JSON</h2>
          </div>
          <pre id="json-output">{}</pre>
        </div>
      </section>
    </main>

    <script src="/static/app.js"></script>
  </body>
</html>
```

- [ ] **Step 2: Create CSS**

Create `app/static/styles.css`:

```css
:root {
  color-scheme: light;
  --bg: #f6f7f9;
  --panel: #ffffff;
  --text: #17202a;
  --muted: #667085;
  --line: #d8dee8;
  --accent: #1f7a5c;
  --accent-soft: #e7f4ef;
  --danger: #b42318;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-height: 100vh;
  background: var(--bg);
  color: var(--text);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.shell {
  width: min(1180px, calc(100vw - 32px));
  margin: 32px auto;
}

.workspace {
  display: grid;
  grid-template-columns: 360px minmax(0, 1fr);
  gap: 24px;
  align-items: start;
}

.controls,
.output {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 20px;
}

h1,
h2 {
  margin: 0 0 16px;
  line-height: 1.2;
}

h1 {
  font-size: 28px;
}

h2 {
  font-size: 18px;
}

label {
  display: grid;
  gap: 8px;
  margin-bottom: 16px;
  color: var(--muted);
  font-size: 14px;
}

select,
button {
  width: 100%;
  min-height: 42px;
  border-radius: 6px;
  border: 1px solid var(--line);
  font: inherit;
}

select {
  padding: 0 12px;
  background: #fff;
  color: var(--text);
}

button {
  cursor: pointer;
  border-color: var(--accent);
  background: var(--accent);
  color: #fff;
  font-weight: 650;
}

button:disabled {
  cursor: wait;
  opacity: 0.7;
}

.drop-zone {
  display: grid;
  place-items: center;
  min-height: 170px;
  padding: 20px;
  border: 2px dashed var(--line);
  border-radius: 8px;
  background: #fbfcfd;
  color: var(--muted);
  text-align: center;
  cursor: pointer;
}

.drop-zone.is-dragover,
.drop-zone.has-file {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.drop-zone.is-invalid {
  border-color: var(--danger);
  background: #fff1f0;
}

.drop-title {
  display: block;
  color: var(--text);
  font-weight: 700;
}

.drop-meta {
  display: block;
  margin-top: 4px;
  font-size: 13px;
}

#file-input {
  position: absolute;
  inline-size: 1px;
  block-size: 1px;
  opacity: 0;
  pointer-events: none;
}

#status {
  min-height: 22px;
  margin: 14px 0 0;
  color: var(--muted);
}

#status.is-error {
  color: var(--danger);
}

.output-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

#json-output {
  min-height: 560px;
  max-height: calc(100vh - 170px);
  overflow: auto;
  margin: 0;
  padding: 16px;
  border-radius: 6px;
  background: #101828;
  color: #e4e7ec;
  font-size: 13px;
  line-height: 1.55;
}

@media (max-width: 820px) {
  .workspace {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Step 3: Create browser JavaScript**

Create `app/static/app.js`:

```javascript
const allowedExtensions = [".pdf", ".docx", ".doc"];

const dropZone = document.querySelector("#drop-zone");
const fileInput = document.querySelector("#file-input");
const fileName = document.querySelector("#file-name");
const providerSelect = document.querySelector("#provider-select");
const modelSelect = document.querySelector("#model-select");
const parseButton = document.querySelector("#parse-button");
const statusText = document.querySelector("#status");
const jsonOutput = document.querySelector("#json-output");

let selectedFile = null;
let providers = [];

function setStatus(message, isError = false) {
  statusText.textContent = message;
  statusText.classList.toggle("is-error", isError);
}

function extensionOf(name) {
  const index = name.lastIndexOf(".");
  return index === -1 ? "" : name.slice(index).toLowerCase();
}

function setSelectedFile(file) {
  const extension = extensionOf(file.name);
  if (!allowedExtensions.includes(extension)) {
    selectedFile = null;
    fileInput.value = "";
    dropZone.classList.remove("has-file");
    dropZone.classList.add("is-invalid");
    fileName.textContent = "Unsupported file. Use PDF, DOCX, or DOC.";
    setStatus("Unsupported file type. Please choose a PDF, DOCX, or DOC file.", true);
    return;
  }

  selectedFile = file;
  dropZone.classList.remove("is-invalid");
  dropZone.classList.add("has-file");
  fileName.textContent = file.name;
  setStatus("");
}

function updateModelOptions() {
  const selectedProvider = providers.find((provider) => provider.id === providerSelect.value);
  modelSelect.innerHTML = "";

  if (!selectedProvider || !selectedProvider.available) {
    modelSelect.disabled = true;
    return;
  }

  modelSelect.disabled = false;
  for (const model of selectedProvider.models) {
    const option = document.createElement("option");
    option.value = model;
    option.textContent = model;
    modelSelect.appendChild(option);
  }
}

async function loadModels() {
  const response = await fetch("/api/models");
  const payload = await response.json();
  providers = payload.providers;
  providerSelect.innerHTML = "";

  for (const provider of providers) {
    const option = document.createElement("option");
    option.value = provider.id;
    option.textContent = provider.available ? provider.label : `${provider.label} (unavailable)`;
    option.disabled = !provider.available;
    providerSelect.appendChild(option);
  }

  updateModelOptions();
}

dropZone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropZone.classList.add("is-dragover");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("is-dragover");
});

dropZone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropZone.classList.remove("is-dragover");
  const file = event.dataTransfer.files[0];
  if (file) {
    setSelectedFile(file);
  }
});

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (file) {
    setSelectedFile(file);
  }
});

providerSelect.addEventListener("change", updateModelOptions);

parseButton.addEventListener("click", async () => {
  if (!selectedFile) {
    setStatus("Choose a resume file first.", true);
    return;
  }

  const formData = new FormData();
  formData.append("file", selectedFile);
  formData.append("provider", providerSelect.value);
  formData.append("model", modelSelect.value);

  parseButton.disabled = true;
  setStatus("Parsing resume...");

  try {
    const response = await fetch("/api/parse", {
      method: "POST",
      body: formData,
    });
    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.detail || "Resume parsing failed.");
    }

    jsonOutput.textContent = JSON.stringify(payload.data, null, 2);
    setStatus("Parsed successfully.");
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    parseButton.disabled = false;
  }
});

loadModels().catch((error) => {
  setStatus(error.message, true);
});
```

- [ ] **Step 4: Run API tests**

Run:

```powershell
uv run pytest tests/test_api.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit FastAPI and UI**

Run:

```powershell
git add app/main.py app/templates/index.html app/static/styles.css app/static/app.js tests/test_api.py
git commit -m "feat: add fastapi upload ui"
```

## Task 10: OCR Integration in Parse Flow

**Files:**
- Modify: `tests/test_api.py`

- [ ] **Step 1: Add API test proving OCR append flow**

Append this test to `tests/test_api.py`:

```python
def test_parse_appends_ocr_when_triggered(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    seen = {}

    async def fake_parse_resume_markdown(markdown: str, provider: str, model: str, settings):
        seen["markdown"] = markdown
        return ResumeData(raw_markdown_preview=markdown[:500])

    monkeypatch.setattr("app.main.convert_resume_file", lambda path: type("Doc", (), {"markdown": "# Jane"})())
    monkeypatch.setattr("app.main.should_run_ocr", lambda path, markdown, settings: True)
    monkeypatch.setattr(
        "app.main.run_tesseract_ocr",
        lambda path, settings: type("Ocr", (), {"text": "OCR phone", "attempted": True})(),
    )
    monkeypatch.setattr("app.main.parse_resume_markdown", fake_parse_resume_markdown)

    response = client.post(
        "/api/parse",
        data={"provider": "local_ollama", "model": "llama3.2"},
        files={"file": ("resume.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )

    assert response.status_code == 200
    assert "## OCR Extracted Text" in seen["markdown"]
    assert "OCR phone" in seen["markdown"]
```

- [ ] **Step 2: Run API tests**

Run:

```powershell
uv run pytest tests/test_api.py -v
```

Expected: PASS.

- [ ] **Step 3: Commit**

Run:

```powershell
git add tests/test_api.py
git commit -m "test: cover ocr parse integration"
```

## Task 11: Full Verification and Cleanup

**Files:**
- Modify only files required by failures found in this task.

- [ ] **Step 1: Run formatter/linter**

Run:

```powershell
uv run ruff check .
```

Expected: PASS. If it fails, fix only the reported lint issues.

- [ ] **Step 2: Run test suite**

Run:

```powershell
uv run pytest -v
```

Expected: PASS.

- [ ] **Step 3: Start the app locally**

Run:

```powershell
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Expected:

```text
Uvicorn running on http://127.0.0.1:8000
```

Manual browser checks:

- `GET /` loads the UI.
- Dragging a `.pdf`, `.docx`, or `.doc` onto the upload area shows the filename.
- Dragging a `.txt` shows an unsupported file error.
- Provider dropdown loads local Ollama by default.
- Gemini is disabled or hidden when no key is configured.
- JSON output area updates after a mocked or real parse.

- [ ] **Step 4: Final commit for fixes**

If Step 1 or Step 2 required fixes, run:

```powershell
git add app tests README.md pyproject.toml .env.example
git commit -m "chore: verify resume parser"
```

If no files changed, skip this commit.

## Self-Review

Spec coverage:

- FastAPI backend: Tasks 8 and 9.
- Plain HTML UI: Task 9.
- Drag-and-drop upload with file picker fallback: Task 9.
- PDF, DOCX, best-effort DOC validation: Task 5.
- MarkItDown conversion: Task 5.
- Tesseract OCR trigger and append behavior: Tasks 6 and 10.
- Pydantic schemas: Task 3.
- Pydantic AI parser: Task 7.
- Local Ollama, cloud Ollama, Gemini option: Tasks 2 and 7.
- Gemini only when API key is present: Task 2.
- JSON output rendering: Task 9.
- Error handling: Tasks 4, 5, 6, 8.
- Tests: Tasks 2, 3, 5, 6, 7, 8, 10, 11.

Placeholder scan:

- No implementation step uses placeholder-only instructions.
- Deferred OCR rendering for PDFs/DOCX is explicitly bounded behind `run_tesseract_ocr()` with tests for the public contract. If full page rendering is required after real fixtures are tested, extend only that function without changing API boundaries.

Type consistency:

- Provider IDs are consistently `local_ollama`, `cloud_ollama`, and `gemini`.
- Model registry response uses `providers`.
- Parse response uses `provider`, `model`, `filename`, and `data`.
- Resume schema uses `raw_markdown_preview`.
- OCR append heading is consistently `## OCR Extracted Text`.

