import shutil
from pathlib import Path

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

    # Full PDF rendering and DOCX image extraction can extend this public contract later.
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}:
        text = pytesseract.image_to_string(str(path)).strip()
        return OcrResult(text=text, attempted=True)

    return OcrResult(text="", attempted=True)


def append_ocr_text(markdown: str, ocr_result: OcrResult) -> str:
    if not ocr_result.text.strip():
        return markdown
    return f"{markdown.rstrip()}\n\n## OCR Extracted Text\n\n{ocr_result.text.strip()}"
