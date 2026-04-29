from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


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
    local_ollama_models: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["qwen3.5:0.8b-q8_0"]
    )

    cloud_ollama_base_url: str = ""
    cloud_ollama_api_key: str = ""
    cloud_ollama_models: Annotated[list[str], NoDecode] = Field(default_factory=list)

    gemini_api_key: str = ""
    google_api_key: str = ""
    gemini_models: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["gemini-2.5-flash"]
    )

    @field_validator("local_ollama_models", "cloud_ollama_models", "gemini_models", mode="before")
    @classmethod
    def parse_model_list(cls, value: object) -> object:
        if isinstance(value, str):
            return [model.strip() for model in value.split(",") if model.strip()]
        return value

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def has_gemini_key(self) -> bool:
        return bool(self.gemini_api_key or self.google_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
