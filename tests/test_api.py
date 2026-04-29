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
