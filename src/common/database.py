
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.common.config import get_settings


def get_engine() -> Engine:
    settings = get_settings()
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        connect_args={"connect_timeout": 10},
    )


def check_database_connection() -> bool:
    engine = get_engine()

    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar_one()
            return result == 1
    finally:
        engine.dispose()
