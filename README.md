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
