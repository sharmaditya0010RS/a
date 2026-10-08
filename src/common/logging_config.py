
import logging

from src.common.config import ROOT_DIR, get_settings


def configure_logging() -> logging.Logger:
    settings = get_settings()
    log_directory = ROOT_DIR / "logs"
    log_directory.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("financial_crime_intelligence")
    logger.setLevel(settings.log_level.upper())

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = logging.FileHandler(
        log_directory / "application.log",
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger
