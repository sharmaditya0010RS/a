
from pathlib import Path

from sqlalchemy import create_engine, text

from src.common.config import get_settings


def test_raw_schema_file_exists():
    assert Path("sql/raw/001_create_raw_schema.sql").is_file()


def test_raw_tables_exist():
    engine = create_engine(get_settings().database_url)

    try:
        with engine.connect() as connection:
            result = connection.execute(
                text(
                    "SELECT "
                    "to_regclass('raw.transactions') IS NOT NULL "
                    "AND to_regclass('raw.ingestion_batches') IS NOT NULL"
                )
            ).scalar_one()

        assert result is True

    finally:
        engine.dispose()
