from ..main_registry import MainRegistry
from ...config.pkg_config import PkgConfig
from ..front_mater_meta import FrontMatterMeta


class RegistryCreator:
    def __init__(self, main_registry: MainRegistry, template_meta: FrontMatterMeta):
        self.main_registry = main_registry
        self.config = PkgConfig()
        self._fm = template_meta
