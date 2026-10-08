
import pytest

from src.common.config import ROOT_DIR, get_settings


def test_project_root_exists():
    assert ROOT_DIR.is_dir()


def test_default_environment(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    assert get_settings().app_env == "development"


def test_positive_chunk_size(monkeypatch):
    monkeypatch.setenv("CHUNK_SIZE", "1000")
    assert get_settings().chunk_size == 1000


def test_invalid_chunk_size(monkeypatch):
    monkeypatch.setenv("CHUNK_SIZE", "0")

    with pytest.raises(ValueError, match="positive"):
        get_settings()


def test_raw_data_path_absolute():
    assert get_settings().raw_data_path.is_absolute()
