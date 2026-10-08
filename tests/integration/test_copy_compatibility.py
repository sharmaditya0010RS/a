import io

from sqlalchemy import create_engine

from src.common.config import get_settings


def test_psycopg_copy_api():
    engine = create_engine(get_settings().database_url)

    try:
        raw_connection = engine.raw_connection()

        try:
            cursor = raw_connection.cursor()

            try:
                cursor.execute(
                    "CREATE TEMP TABLE copy_compatibility_test "
                    "(value TEXT)"
                )

                with cursor.copy(
                    "COPY copy_compatibility_test (value) "
                    "FROM STDIN WITH (FORMAT CSV)"
                ) as copy:
                    copy.write(io.StringIO("copy_api_verified\n").getvalue())

                cursor.execute(
                    "SELECT value FROM copy_compatibility_test"
                )

                result = cursor.fetchone()

                assert result is not None
                assert result[0] == "copy_api_verified"

                raw_connection.rollback()

            finally:
                cursor.close()

        finally:
            raw_connection.close()

    finally:
        engine.dispose()