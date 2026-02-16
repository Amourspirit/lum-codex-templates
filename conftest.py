import pytest
from pathlib import Path
# created a root path that points the root path of this file.


@pytest.fixture(scope="session")
def root_path():
    import os

    return Path(os.path.dirname(__file__)).parent


@pytest.fixture(scope="session")
def current_monad_name():
    return "Soluun"
