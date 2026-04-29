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
        raise FileValidationError(
            f"File is too large. Maximum size is {settings.max_upload_mb} MB."
        )


def convert_resume_file(path: Path) -> ConvertedDocument:
    try:
        result = MarkItDown(enable_plugins=False).convert(str(path))
    except Exception as exc:
        raise DocumentConversionError(f"Could not convert document with MarkItDown: {exc}") from exc

    markdown = (result.text_content or "").strip()
    if not markdown:
        raise DocumentConversionError(
            "No readable Markdown was produced from the uploaded document."
        )

    return ConvertedDocument(markdown=markdown, markdown_char_count=len(markdown))
