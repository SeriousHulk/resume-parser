import tempfile
from pathlib import Path
from typing import Annotated

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
    return templates.TemplateResponse(request, "index.html")


@app.get("/api/models")
async def models(settings: Annotated[Settings, Depends(get_settings)]):
    return get_model_registry(settings)


@app.post("/api/parse", response_model=ParseResponse)
async def parse_resume(
    file: Annotated[UploadFile, File()],
    provider: Annotated[str, Form()],
    model: Annotated[str, Form()],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ParseResponse:
    content = await file.read()
    try:
        validate_upload_metadata(file.filename or "", len(content), settings)
        if not validate_provider_model(provider, model, settings):
            raise HTTPException(
                status_code=400,
                detail="Selected provider or model is unavailable.",
            )

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
            return ParseResponse(
                provider=provider,
                model=model,
                filename=file.filename or "",
                data=data,
            )
        finally:
            tmp_path.unlink(missing_ok=True)
    except HTTPException:
        raise
    except ResumeParserError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
