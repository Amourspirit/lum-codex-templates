from typing import Any
from pathlib import Path
from ....main_registry import MainRegistry
from .....config.pkg_config import PkgConfig
from ....front_mater_meta import FrontMatterMeta


class EnforcementBase:
    def __init__(
        self,
        working_dir: Path,
        main_registry: MainRegistry,
        templates_data: dict[str, FrontMatterMeta],
    ):
        self.__working_dir = working_dir
        self.__main_registry = main_registry
        self.__config = PkgConfig()
        self.__templates_data = templates_data

    @property
    def config(self) -> PkgConfig:
        return self.__config

    @property
    def main_registry(self) -> MainRegistry:
        return self.__main_registry

    @property
    def working_dir(self) -> Path:
        return self.__working_dir

    @property
    def templates_data(self) -> dict[str, FrontMatterMeta]:
        return self.__templates_data
