import pytest

from src.config.pkg_config import PkgConfig


@pytest.fixture(scope="session")
def pkg_config():
    return PkgConfig()


@pytest.fixture(scope="session")
def current_monad_name(pkg_config: PkgConfig):
    return pkg_config.current_user
