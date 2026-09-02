import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "OmniCalc AI"
    app_version: str = "0.2.0"
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "").strip()
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5-mini").strip()
    database_url: str = os.getenv("DATABASE_URL", "").strip()
    allowed_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    )


settings = Settings()
