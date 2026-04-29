# Resume Parser Project Specification

## 1. Overview

The resume parser project is a small web application that extracts structured information from uploaded resume files and returns the result as JSON. The application will support common resume formats, use a transformer-backed LLM through the Pydantic AI library, and provide a simple HTML interface for uploading a file, selecting a model provider, and viewing the extracted JSON.

This project is intentionally limited in scope. It is not a full applicant tracking system, candidate database, ranking engine, or enterprise document management platform. The goal is to build a clean, understandable parser that demonstrates document ingestion, model-backed extraction, validation, and JSON output.

## 2. Goals

- Accept resume uploads from a simple browser UI with both drag-and-drop and standard file selection.
- Support `.pdf`, `.docx`, and legacy Word document uploads where feasible.
- Convert uploaded resumes to Markdown using Microsoft MarkItDown.
- Run a Tesseract OCR pass when image-only or embedded-image content is detected.
- Use Pydantic AI to call a selected LLM provider.
- Support local Ollama models.
- Support cloud-hosted Ollama-compatible models.
- Support Gemini API when an API key is provided.
- Return structured JSON validated by Pydantic models.
- Show extracted JSON in the UI.
- Keep the backend small, testable, and easy to run locally.

## 3. Non-Goals

- No authentication or user accounts.
- No persistent candidate database in the initial version.
- No resume ranking, scoring, or job matching.
- No multi-file batch processing in the initial UI.
- No advanced admin dashboard.
- No long-term file storage.
- No training or fine-tuning of transformer models.
- No full OCR pipeline for every upload by default.
- No separate PDF or Word text extraction libraries in the first version; document ingestion should go through MarkItDown.
- No LLM-vision OCR plugin in the first version; OCR support should use Tesseract.
- No complex frontend framework unless later required.

## 4. High-Level User Flow

1. User opens the local web UI.
2. User selects a resume file by dragging it into the upload area or using the file picker.
3. User chooses a model provider and model from the model switcher.
4. User clicks parse.
5. Backend validates the file type and converts the resume to Markdown with MarkItDown.
6. Backend detects whether the document likely contains image-only or embedded-image content.
7. If needed, backend runs a Tesseract OCR pass and appends OCR text to the converted Markdown.
8. Backend sends the combined Markdown content to the selected model through Pydantic AI.
9. Model returns structured resume data.
10. Backend validates and normalizes the response with Pydantic schemas.
11. UI displays the extracted JSON.

## 5. Application Architecture

The project will use a small FastAPI backend and a plain HTML/CSS/JavaScript frontend.

### Backend

The backend will be responsible for:

- Serving the HTML UI.
- Receiving uploaded resume files.
- Validating file extension and file size.
- Converting supported document formats to Markdown with MarkItDown.
- Calling the selected LLM provider through Pydantic AI.
- Validating the extracted result with Pydantic models.
- Returning JSON responses to the frontend.

Recommended backend structure:

```text
app/
  main.py
  config.py
  schemas.py
  document_converter.py
  ocr.py
  parser_agent.py
  model_registry.py
  templates/
    index.html
  static/
    styles.css
    app.js
tests/
  test_document_converter.py
  test_ocr.py
  test_schemas.py
  test_parser_agent.py
```

### Frontend

The frontend will be a simple HTML page with:

- Drag-and-drop upload area.
- Standard file upload input as a fallback.
- Model provider selector.
- Model selector.
- Parse button.
- Loading/error state.
- JSON output section.

The upload area should provide clear visual states for idle, drag-over, selected file, invalid file type, and upload/parsing in progress. The UI should be practical and minimal. It should not include marketing pages, user dashboards, or unrelated views.

## 6. Document Conversion

The project will use Microsoft MarkItDown as the primary document ingestion layer.

MarkItDown converts uploaded files into Markdown, which is a better intermediate format for LLM extraction than plain text because it can preserve useful structure such as headings, lists, tables, and links. The parser agent will receive this Markdown content rather than raw binary files or parser-specific text fragments. If a Tesseract OCR pass is triggered, the OCR result will be appended as a clearly labeled Markdown section.

Source:

- `https://github.com/microsoft/markitdown`

### Dependency

The initial document conversion dependency should be:

```text
markitdown[pdf,docx]
```

The broader `markitdown[all]` extra may be used during local experimentation, but the project spec prefers the narrowest useful dependency set for this app.

The OCR dependencies should be:

```text
pytesseract
Pillow
```

The system must also have the Tesseract binary installed and available on `PATH`, or configured through an explicit executable path.

### Conversion API

The backend should prefer MarkItDown's local or stream conversion API instead of broad remote URL conversion.

Recommended behavior:

- Save the upload to a controlled temporary path or pass a bounded stream to MarkItDown.
- Call the narrowest MarkItDown conversion method that fits the implementation.
- Do not let user-controlled input cause MarkItDown to fetch arbitrary URLs.
- Treat the returned Markdown as the source text for the Pydantic AI parser.
- Return a helpful error if MarkItDown returns empty or unusable content.
- After conversion, pass the original file and converted Markdown through OCR trigger detection.

### PDF

PDF support should be implemented through MarkItDown.

Initial behavior:

- Convert standard digital PDFs to Markdown.
- Preserve useful headings, lists, and tables where MarkItDown can identify them.
- Return a helpful error if no usable Markdown content is produced.

### DOCX

DOCX support should be implemented through MarkItDown.

Initial behavior:

- Convert `.docx` files to Markdown.
- Preserve useful headings, lists, tables, and links where MarkItDown can identify them.
- Return a helpful error if conversion fails or produces no useful content.

### DOC / Legacy Word

Legacy `.doc` support should also go through MarkItDown if the installed MarkItDown dependencies and runtime can handle the file.

Initial behavior should be conservative:

- Accept `.doc` uploads at the API validation layer.
- Attempt conversion through MarkItDown.
- Return a clear unsupported-conversion error if MarkItDown cannot process the specific legacy Word file.

The project should not add a second `.doc` extraction stack just to improve legacy coverage in the initial version.

### OCR

MarkItDown has an optional `markitdown-ocr` plugin, but that plugin uses LLM vision rather than Tesseract. This project should not use the MarkItDown OCR plugin in the first version.

Instead, the first version should add a targeted Tesseract OCR pass only when image content appears relevant.

OCR trigger conditions:

- MarkItDown produces very little usable Markdown.
- The uploaded PDF appears to have image-only pages or no extractable text.
- The uploaded DOCX contains embedded images.
- MarkItDown output includes image placeholders without meaningful text nearby.
- File metadata or conversion diagnostics indicate embedded images.

OCR behavior:

- Run OCR only when one of the trigger conditions is met.
- Use Tesseract through `pytesseract`.
- Convert detected images or image-only pages to images that Tesseract can read.
- Append OCR output under a clearly labeled Markdown heading such as `## OCR Extracted Text`.
- Do not overwrite MarkItDown output.
- If OCR fails, continue with MarkItDown output when it contains enough text.
- If both MarkItDown and OCR produce no usable text, return a clear "no readable text found" error.
- If Tesseract is not installed and OCR is required, return a clear configuration error.

Recommended OCR helpers:

- For embedded image files: use `Pillow` and `pytesseract`.
- For image-only PDFs: use a small, explicit PDF page rendering dependency only for OCR fallback if required by implementation.

The OCR pass should be treated as a supplement to MarkItDown, not as the primary document parser.

## 7. Model Provider Support

The parser will use Pydantic AI as the main abstraction for model calls and structured extraction.

### Local Ollama

Local Ollama is the default development provider.

Expected configuration:

- Base URL: `http://localhost:11434`
- Model examples:
  - `llama3.2`
  - `qwen3`
  - `mistral`
  - any locally installed Ollama model

The model switcher should allow known configured models and may also allow a custom model name if simple to support.

### Cloud Ollama-Compatible Provider

Cloud Ollama support means an Ollama-compatible hosted endpoint can be configured.

Expected configuration:

- `CLOUD_OLLAMA_BASE_URL`
- `CLOUD_OLLAMA_API_KEY`, if required by the provider
- `CLOUD_OLLAMA_MODELS`, comma-separated

The backend should not hard-code one cloud provider. It should use Pydantic AI's Ollama provider with configurable `base_url` and optional `api_key`.

### Gemini API

Gemini should be available only when a Gemini API key is configured. In Pydantic AI this should be implemented with `GoogleModel` using the Gemini Generative Language API.

Expected configuration:

- `GEMINI_API_KEY`, accepted by this app
- `GOOGLE_API_KEY`, optional alias compatible with Pydantic AI defaults
- `GEMINI_MODELS`, comma-separated

If no Gemini API key is provided:

- Gemini should either be hidden from the UI provider list or shown as disabled.
- The backend must reject Gemini requests with a clear configuration error.

## 8. Model Switcher Behavior

The UI should expose two related controls:

- Provider selector:
  - Local Ollama
  - Cloud Ollama
  - Gemini
- Model selector:
  - Populated from backend configuration for the selected provider.

The frontend should call a backend endpoint such as:

```http
GET /api/models
```

Example response:

```json
{
  "providers": [
    {
      "id": "local_ollama",
      "label": "Local Ollama",
      "available": true,
      "models": ["llama3.2", "qwen3"]
    },
    {
      "id": "cloud_ollama",
      "label": "Cloud Ollama",
      "available": true,
      "models": ["llama3.2-cloud"]
    },
    {
      "id": "gemini",
      "label": "Gemini",
      "available": false,
      "models": []
    }
  ]
}
```

The parse request should include provider and model:

```http
POST /api/parse
```

Form fields:

- `file`: uploaded resume file
- `provider`: selected provider ID
- `model`: selected model name

## 9. Extracted JSON Schema

The parser should return a predictable JSON shape even when some fields are missing.

Recommended top-level schema:

```json
{
  "contact": {
    "name": "string | null",
    "email": "string | null",
    "phone": "string | null",
    "location": "string | null",
    "links": ["string"]
  },
  "summary": "string | null",
  "education": [
    {
      "institution": "string | null",
      "degree": "string | null",
      "field_of_study": "string | null",
      "graduation_year": "string | null",
      "start_date": "string | null",
      "end_date": "string | null"
    }
  ],
  "work_experience": [
    {
      "company": "string | null",
      "position": "string | null",
      "location": "string | null",
      "start_date": "string | null",
      "end_date": "string | null",
      "duration": "string | null",
      "description": "string | null",
      "highlights": ["string"]
    }
  ],
  "skills": ["string"],
  "certifications": [
    {
      "name": "string | null",
      "issuer": "string | null",
      "year": "string | null"
    }
  ],
  "projects": [
    {
      "name": "string | null",
      "description": "string | null",
      "technologies": ["string"],
      "links": ["string"]
    }
  ],
  "languages": ["string"],
  "raw_markdown_preview": "string"
}
```

Pydantic models should define this schema. The model should be instructed to return only data that is present or reasonably inferable from the resume text. Unknown values should be `null` or empty arrays instead of hallucinated details.

## 10. Pydantic AI Agent Design

The parser agent should:

- Accept converted resume Markdown, optionally supplemented with Tesseract OCR text.
- Accept provider and model selection.
- Use a strict output schema.
- Prompt the model to extract structured resume data.
- Avoid inventing missing information.
- Normalize arrays and nullable fields.
- Return validated Pydantic output.

Pydantic AI output mode:

- Prefer structured output through Pydantic AI using the resume schema.
- Use the default tool-based output mode where it is the most portable provider choice.
- Avoid relying only on provider-enforced JSON schema output for cloud Ollama, because hosted Ollama-compatible endpoints may accept schema settings without enforcing them consistently.

Prompt guidance:

- The model is an information extraction assistant.
- The source of truth is the converted resume Markdown and any clearly labeled OCR text appended by the backend.
- Do not infer facts that are not present.
- Keep descriptions concise.
- Preserve dates as written when normalization is uncertain.
- Return valid structured output matching the schema.

The agent should not decide file handling or OCR strategy. It receives Markdown content only.

## 11. Configuration

Configuration should be environment-driven.

Suggested environment variables:

```text
APP_NAME=Resume Parser
MAX_UPLOAD_MB=10
ENABLE_OCR=true
TESSERACT_CMD=
OCR_MIN_MARKDOWN_CHARS=200

LOCAL_OLLAMA_BASE_URL=http://localhost:11434
LOCAL_OLLAMA_MODELS=llama3.2,qwen3

CLOUD_OLLAMA_BASE_URL=
CLOUD_OLLAMA_API_KEY=
CLOUD_OLLAMA_MODELS=

GEMINI_API_KEY=
GOOGLE_API_KEY=
GEMINI_MODELS=gemini-2.5-flash
```

The app should include an `.env.example` with safe placeholder values.

## 12. API Endpoints

### `GET /`

Serves the HTML UI.

### `GET /api/models`

Returns available providers and model names based on configuration.

### `POST /api/parse`

Accepts one resume file plus provider/model fields and returns parsed JSON.

Success response:

```json
{
  "provider": "local_ollama",
  "model": "llama3.2",
  "filename": "resume.pdf",
  "data": {
    "contact": {
      "name": "Jane Doe",
      "email": "jane@example.com",
      "phone": "+1 555 123 4567",
      "location": "New York, NY",
      "links": ["https://linkedin.com/in/janedoe"]
    },
    "summary": "Backend engineer with experience in Python APIs.",
    "education": [],
    "work_experience": [],
    "skills": ["Python", "FastAPI"],
    "certifications": [],
    "projects": [],
    "languages": [],
    "raw_markdown_preview": "Jane Doe..."
  }
}
```

Error response:

```json
{
  "detail": "Unsupported file type. Please upload a PDF, DOCX, or DOC file."
}
```

## 13. Error Handling

The application should return clear errors for:

- Missing file.
- Unsupported file extension.
- File too large.
- Empty converted Markdown.
- OCR required but Tesseract is unavailable.
- OCR produced no readable text.
- Provider unavailable.
- Model unavailable.
- Missing Gemini API key.
- Cloud Ollama configuration missing.
- Model response validation failure.
- Unexpected parser failure.

The frontend should show errors near the upload area and keep the JSON output area unchanged until a successful parse completes.

## 14. Validation and Normalization

Validation should happen in two layers:

1. Request validation:
   - file exists
   - extension is allowed
   - size is under configured limit
   - provider/model combination is allowed

2. Output validation:
   - LLM response matches the Pydantic resume schema
   - nullable fields remain nullable
   - list fields default to empty lists
   - malformed model output is rejected with a helpful error

The app should not silently return invalid JSON.

## 15. Security and Privacy

Since resumes contain personal information, the app should be cautious by default.

Initial security expectations:

- Do not persist uploaded resumes unless explicitly configured later.
- Store temporary files only as needed during parsing.
- Delete temporary files after processing.
- Do not log full resume text.
- Do not log extracted personal data.
- Make it clear that selecting cloud Ollama or Gemini sends resume text to an external API.

No authentication is required for the first version because the target use is local or controlled development.

## 16. Testing Strategy

Tests should focus on the parts that can be verified without depending on live model output.

Recommended tests:

- Pydantic schema validation.
- File extension validation.
- Upload size validation.
- MarkItDown PDF conversion with a small fixture.
- MarkItDown DOCX conversion with a small fixture.
- MarkItDown conversion error handling for unsupported or unreadable files.
- OCR trigger detection for low-text or image-containing documents.
- Tesseract OCR text append behavior with mocked OCR output.
- Graceful behavior when Tesseract is unavailable.
- Model registry availability logic.
- Gemini hidden/unavailable behavior when no API key is configured.
- API error responses for unsupported files.
- Parser agent behavior with mocked model responses.

Live model tests should be optional and not required in the default test suite.

## 17. Minimal Milestones

### Milestone 1: Project Skeleton

- FastAPI app.
- Static HTML UI.
- `.env.example`.
- Model registry endpoint.

### Milestone 2: Document Conversion

- MarkItDown integration.
- PDF-to-Markdown conversion.
- DOCX-to-Markdown conversion.
- Clear `.doc` conversion failure behavior.
- Tesseract OCR fallback for image-only or image-containing documents.
- Unit tests for document conversion.

### Milestone 3: Pydantic Resume Schema

- Define output models.
- Add validation tests.
- Add sample expected JSON.

### Milestone 4: Pydantic AI Integration

- Local Ollama provider.
- Gemini provider when API key exists.
- Cloud Ollama provider from configuration.
- Mocked parser tests.

### Milestone 5: End-to-End UI Flow

- Upload resume with drag-and-drop.
- Upload resume with the standard file picker.
- Select provider/model.
- Parse.
- Render formatted JSON.
- Display loading and error states.

## 18. Acceptance Criteria

The project is complete for the initial limited scope when:

- A user can run the FastAPI app locally.
- The browser UI loads at `/`.
- The UI shows drag-and-drop upload, file picker fallback, provider, model, parse button, and JSON output sections.
- Dragging a supported resume file into the upload area selects it for parsing.
- Dragging an unsupported file shows a clear validation error before parsing.
- `.pdf` and `.docx` files can be converted through MarkItDown and parsed.
- `.doc` files either convert successfully through MarkItDown or return a clear unsupported-conversion message.
- Documents with detected image-only or embedded-image content trigger a Tesseract OCR pass.
- OCR text is appended to the Markdown sent to the parser, not used as a replacement for MarkItDown output.
- Local Ollama models are available through the model switcher.
- Cloud Ollama models appear when configured.
- Gemini appears only when `GEMINI_API_KEY` is configured.
- Parsed output is returned as validated JSON matching the resume schema.
- Errors are clear and do not expose secrets or full resume text.
- Tests cover document conversion, schemas, registry behavior, and main API errors.

## 19. Deferred Enhancements

The following features are useful but outside the first version:

- LLM-vision OCR using MarkItDown OCR plugins or Azure Document Intelligence.
- Advanced OCR tuning, custom language packs, and confidence-based OCR correction.
- Batch resume parsing.
- Candidate database.
- Export to CSV.
- Resume comparison against job descriptions.
- Authentication.
- Admin configuration UI.
- Fine-tuned extraction model.
- Background job queue for large files.
- Streaming parse status.
