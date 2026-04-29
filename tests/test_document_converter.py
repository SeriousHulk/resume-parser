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
        def __init__(self, enable_plugins: bool) -> None:
            assert enable_plugins is False

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
        def __init__(self, enable_plugins: bool) -> None:
            assert enable_plugins is False

        def convert(self, file_path: str) -> FakeResult:
            return FakeResult()

    monkeypatch.setattr("app.document_converter.MarkItDown", FakeMarkItDown)

    with pytest.raises(DocumentConversionError, match="No readable Markdown"):
        convert_resume_file(path)
