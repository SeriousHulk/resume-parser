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

## Provider Configuration

Edit `.env` after copying `.env.example`.

### Local Ollama

Use this when you have Ollama running on your machine.

```text
LOCAL_OLLAMA_BASE_URL=http://localhost:11434
LOCAL_OLLAMA_MODELS=["qwen3.5:0.8b-q8_0","ministral-3:3b"]
```

- `LOCAL_OLLAMA_BASE_URL` should point to your local Ollama server. The app automatically uses Ollama's OpenAI-compatible `/v1` endpoint.
- `LOCAL_OLLAMA_MODELS` is the list shown in the UI for the Local Ollama provider.
- Model values must match names available to your Ollama server, such as the output from `ollama list`.

You can also define a shared list for both Ollama providers:

```text
OLLAMA_MODELS=["gpt-oss:20b-cloud","gemma4:31b-cloud"]
```

If `LOCAL_OLLAMA_MODELS` or `CLOUD_OLLAMA_MODELS` is blank, the app falls back to `OLLAMA_MODELS`.

### Cloud Ollama

Use this for Ollama Cloud or another hosted Ollama-compatible endpoint.

```text
CLOUD_OLLAMA_BASE_URL=https://ollama.com
CLOUD_OLLAMA_API_KEY=your_ollama_cloud_api_key
CLOUD_OLLAMA_MODELS=["gpt-oss:20b-cloud","gemma4:31b-cloud"]
```

- `CLOUD_OLLAMA_BASE_URL` is required for the Cloud Ollama provider to appear as available.
- `CLOUD_OLLAMA_API_KEY` is required if your hosted endpoint needs authentication.
- `CLOUD_OLLAMA_MODELS` is the list shown in the UI for the Cloud Ollama provider.

### Gemini

Use Gemini by setting either `GEMINI_API_KEY` or `GOOGLE_API_KEY`.

```text
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_API_KEY=
GEMINI_MODELS=["gemini-2.5-flash"]
```

- `GEMINI_API_KEY` and `GOOGLE_API_KEY` are interchangeable for this app; set one of them.
- Leave both blank to hide/disable Gemini in the UI.
- `GEMINI_MODELS` can be a JSON list or a single comma-separated value.

## Run

```powershell
uv run uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Test

```powershell
uv run pytest -v
```
