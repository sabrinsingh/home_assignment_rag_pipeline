# tests/conftest.py
import pytest
from unittest.mock import MagicMock

# Mocking the MinIO client and safe_get function used in scraper.py
@pytest.fixture
def mock_safe_get():
    with MagicMock() as mock:
        yield mock

@pytest.fixture
def mock_minio_client():
    minio_mock = MagicMock()
    yield minio_mock

# Optionally, you can mock time.sleep to speed up testing
@pytest.fixture
def mock_sleep(monkeypatch):
    def mock_sleep_fn(seconds):
        pass  # Skip the actual sleep
    monkeypatch.setattr("time.sleep", mock_sleep_fn)
