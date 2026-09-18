import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "OmniCalc AI"
    app_version: str = "1.0.0"
    app_env: str = os.getenv("APP_ENV", "development").strip().lower()
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "").strip()
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5-mini").strip()
    database_url: str = os.getenv("DATABASE_URL", "").strip()
    jwt_secret: str = os.getenv("JWT_SECRET", "development-only-change-this-secret-32-chars").strip()
    jwt_issuer: str = os.getenv("JWT_ISSUER", "omnicalc-api").strip()
    jwt_audience: str = os.getenv("JWT_AUDIENCE", "omnicalc-web").strip()
    access_token_minutes: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "15"))
    refresh_token_days: int = int(os.getenv("REFRESH_TOKEN_DAYS", "30"))
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    cookie_secure: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    cookie_samesite: str = os.getenv("COOKIE_SAMESITE", "lax").lower()
    allowed_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    )

    def validate(self) -> None:
        if self.app_env not in {"development", "test", "production"}:
            raise RuntimeError("APP_ENV must be development, test, or production.")
        if len(self.jwt_secret) < 32:
            raise RuntimeError("JWT_SECRET must contain at least 32 characters.")
        if self.cookie_samesite not in {"lax", "strict", "none"}:
            raise RuntimeError("COOKIE_SAMESITE must be lax, strict, or none.")
        if self.cookie_samesite == "none" and not self.cookie_secure:
            raise RuntimeError("COOKIE_SECURE must be true when COOKIE_SAMESITE is none.")
        if self.app_env == "production":
            if self.jwt_secret == "development-only-change-this-secret-32-chars":
                raise RuntimeError("Production requires a unique JWT_SECRET.")
            if not self.database_url:
                raise RuntimeError("Production requires DATABASE_URL; in-memory persistence is not allowed.")
            if not self.cookie_secure:
                raise RuntimeError("Production requires COOKIE_SECURE=true.")
            if not self.allowed_origins or "*" in self.allowed_origins:
                raise RuntimeError("Production requires explicit ALLOWED_ORIGINS.")


settings = Settings()
settings.validate()
