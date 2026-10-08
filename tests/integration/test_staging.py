from sqlalchemy import create_engine, text

from src.common.config import get_settings


def test_staging_row_reconciliation():
    engine = create_engine(get_settings().database_url)

    try:
        with engine.connect() as connection:
            counts = connection.execute(
                text(
                    "SELECT "
                    "(SELECT COUNT(*) FROM raw.transactions) "
                    "AS raw_count, "
                    "(SELECT COUNT(*) FROM staging.transactions) "
                    "AS staged_count"
                )
            ).mappings().one()

        assert counts["raw_count"] == counts["staged_count"]
        assert counts["staged_count"] == 5078345

    finally:
        engine.dispose()


def test_staging_quality_results():
    engine = create_engine(get_settings().database_url)

    try:
        with engine.connect() as connection:
            total_checks = connection.execute(
                text(
                    "SELECT COUNT(*) FROM staging.quality_results"
                )
            ).scalar_one()

            failed_checks = connection.execute(
                text(
                    "SELECT COUNT(*) FROM staging.quality_results "
                    "WHERE status = 'FAIL'"
                )
            ).scalar_one()

        assert total_checks == 9
        assert failed_checks == 0

    finally:
        engine.dispose()