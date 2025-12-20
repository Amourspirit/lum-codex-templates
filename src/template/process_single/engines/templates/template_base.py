from typing import Any
from ....main_registry import MainRegistry
from .....config.pkg_config import PkgConfig
from ....front_mater_meta import FrontMatterMeta


class TemplateBase:
    def __init__(
        self,
        main_registry: MainRegistry,
        templates_meta: dict[str, dict[str, Any]],
        template_type: str,
    ):
        self.__main_registry = main_registry
        self.__config = PkgConfig()
        self.__meta = templates_meta.get(template_type, {}).copy()
        self._tci = self.config.templates_config_info.tci_items[template_type]

    def _remove_omitted_single_fields(self) -> None:
        omitted_fields = self._tci.single_fields_omitted

        for field in omitted_fields:
            if field in self.template_meta:
                del self.__meta[field]

    def _process_common(self, tokens: dict[str, Any]) -> None:
        # Placeholder for common processing logic
        self.template_meta["template_version"] = self._tci.template_version
        self.template_meta["template_family"] = self._tci.template_family

    @property
    def template_meta(self) -> dict[str, Any]:
        return self.__meta

    @property
    def config(self) -> PkgConfig:
        return self.__config

    @property
    def main_registry(self) -> MainRegistry:
        return self.__main_registry
