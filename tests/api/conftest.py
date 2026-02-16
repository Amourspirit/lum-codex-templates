from __future__ import annotations
from typing import TYPE_CHECKING
import json
import pytest
from pathlib import Path
from api.lib.routes import fn_versions
from src.template.front_mater_meta import FrontMatterMeta

if TYPE_CHECKING:
    from src.config.pkg_config import PkgConfig
else:
    PkgConfig = object


@pytest.fixture(scope="session")
def template_dir(pkg_config: PkgConfig) -> Path:
    return pkg_config.config_cache.get_api_templates_path()


@pytest.fixture(scope="session")
def get_template_fm(template_dir: Path):
    def inner_fn(template_type: str) -> FrontMatterMeta:
        version = fn_versions.get_latest_version_for_template(
            template_type=template_type
        )
        assert version is not None, (
            f"No version found for template type '{template_type}'"
        )
        path = template_dir / template_type / version / "template.md"
        assert path.exists(), f"Template file does not exist at path: {path}"

        fm = FrontMatterMeta(file_path=path)
        return fm

    return inner_fn


@pytest.fixture(scope="session")
def get_template_registry(template_dir: Path):
    def inner_fn(template_type: str) -> dict:
        version = fn_versions.get_latest_version_for_template(
            template_type=template_type
        )
        assert version is not None, (
            f"No version found for template type '{template_type}'"
        )
        path = template_dir / template_type / version / "registry.json"
        assert path.exists(), f"Template file does not exist at path: {path}"

        with open(path, "r") as f:
            registry = json.load(f)
        return registry

    return inner_fn
