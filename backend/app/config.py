from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Configuración SMTP (Opcional, fallback automático a consola)
    SMTP_HOST: Optional[str] = ""
    SMTP_PORT: Optional[int] = 587
    SMTP_USER: Optional[str] = ""
    SMTP_PASSWORD: Optional[str] = ""
    SMTP_FROM: Optional[str] = "noreply@labotik.com"

    class Config:
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"

settings = Settings()