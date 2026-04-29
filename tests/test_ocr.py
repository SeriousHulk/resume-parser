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
