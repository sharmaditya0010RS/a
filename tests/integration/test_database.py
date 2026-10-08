
from sqlalchemy import text

from src.common.database import get_engine


def test_database_connection():
    engine = get_engine()

    try:
        with engine.connect() as connection:
            assert connection.execute(text("SELECT 1")).scalar_one() == 1
    finally:
        engine.dispose()


def test_postgresql_version():
    engine = get_engine()

    try:
        with engine.connect() as connection:
            version = connection.execute(
                text("SHOW server_version")
            ).scalar_one()

        assert version.split(".")[0] == "16"
    finally:
        engine.dispose()
