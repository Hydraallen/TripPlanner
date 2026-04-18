import pytest

from tripplanner.core.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings()
