
import sys

from sqlalchemy import text

from src.common.config import get_settings
from src.common.database import get_engine
from src.common.logging_config import configure_logging


def main() -> int:
    logger = configure_logging()
    settings = get_settings()

    logger.info("Project: %s", settings.app_name)
    logger.info("Environment: %s", settings.app_env)
    logger.info("Version: %s", settings.app_version)

    if sys.version_info[:2] != (3, 12):
        logger.error("Python 3.12 is required")
        return 1

    engine = None

    try:
        engine = get_engine()

        with engine.connect() as connection:
            version = connection.execute(
                text("SHOW server_version")
            ).scalar_one()

            result = connection.execute(
                text("SELECT 1")
            ).scalar_one()

        if result != 1:
            raise RuntimeError("Database health query failed")

        if version.split(".")[0] != "16":
            raise RuntimeError(
                f"Expected PostgreSQL 16, found {version}"
            )

        logger.info("PostgreSQL version: %s", version)
        logger.info("Database connection: PASS")
        logger.info("Environment validation: PASS")
        return 0

    except Exception:
        logger.exception("Environment validation: FAIL")
        return 1

    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    sys.exit(main())
