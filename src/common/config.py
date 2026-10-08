import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_env: str
    app_version: str
    database_url: str
    raw_data_path: Path
    chunk_size: int
    log_level: str


def get_settings() -> Settings:
    raw_path = Path(
        os.getenv("RAW_DATA_PATH", "data/raw/HI-Small_Trans.csv")
    )

    if not raw_path.is_absolute():
        raw_path = ROOT_DIR / raw_path

    chunk_size = int(os.getenv("CHUNK_SIZE", "100000"))

    if chunk_size <= 0:
        raise ValueError("CHUNK_SIZE must be positive")

    return Settings(
        app_name=os.getenv(
            "APP_NAME", "Financial Crime Intelligence Command Center"
        ),
        app_env=os.getenv("APP_ENV", "development"),
        app_version=os.getenv("APP_VERSION", "0.1.0"),
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://aml_user:aml_local_password@127.0.0.1:55432/aml_analytics",
        ),
        raw_data_path=raw_path,
        chunk_size=chunk_size,
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
