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
