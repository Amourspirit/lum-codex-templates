from ..config.pkg_config import PkgConfig
import yaml


class MainRegistry:
    def __init__(self):
        self.config = PkgConfig()
        self._reg = self.load_registry()
        self._reg_id = ""
        self._reg_version = ""
        self._reg_name = ""

    def load_registry(self):
        registry_file = self.config.root_path / self.config.reg_file
        with open(registry_file, "r") as f:
            registry_data = yaml.safe_load(f)
        return registry_data

    # region Properties
    @property
    def reg_id(self) -> str:
        """Gets the registry ID from the loaded registry data."""
        if not self._reg_id:
            self._reg_id = self._reg.get("registry_id", "")
        return self._reg_id

    @property
    def reg_name(self) -> str:
        """Gets the registry name from the loaded registry data."""
        if not self._reg_name:
            self._reg_name = self._reg.get("registery_name", "")
        return self._reg_name

    @property
    def reg_version(self) -> str:
        """Gets the registry version from the loaded registry data."""
        if not self._reg_version:
            self._reg_version = self._reg.get("registry_version", "")
        return self._reg_version

    @property
    def registry(self) -> dict:
        """Gets the entire registry data."""
        return self._reg

    # endregion Properties
