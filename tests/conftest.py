import pytest

from src.config.pkg_config import PkgConfig


@pytest.fixture(scope="session")
def pkg_config():
    return PkgConfig()
