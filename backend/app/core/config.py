import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")


def _get_setting(name: str, default: str) -> str:
    return os.getenv(name, default)


class Settings:
    APP_ENV = _get_setting("APP_ENV", "development")
    DATABASE_URL = _get_setting(
        "DATABASE_URL",
        "mysql+pymysql://root@localhost:3306/council_irs_db?charset=utf8mb4",
    )
    DEFAULT_DEV_SECRET = "local-demo-development-key-replace-with-a-random-secret"
    SECRET_KEY = _get_setting("SECRET_KEY", DEFAULT_DEV_SECRET)
    JWT_ALGORITHM = _get_setting("JWT_ALGORITHM", "HS256")
    JWT_EXP_MINUTES = int(_get_setting("JWT_EXP_MINUTES", "60"))


settings = Settings()
if settings.APP_ENV != "development" and not settings.SECRET_KEY:
    raise RuntimeError("SECRET_KEY must be set in non-development environments.")
if settings.APP_ENV != "development" and settings.SECRET_KEY == settings.DEFAULT_DEV_SECRET:
    raise RuntimeError("Do not use the development JWT secret outside local demo mode.")
