from pathlib import Path
import yaml
from ..config.pkg_config import PkgConfig


class MainRegistry:
    def __init__(self):
        self.config = PkgConfig()
        self._reg: dict = self.load_registry()
        self._reg_id = ""
        self._reg_version = ""
        self._reg_name = ""

    def load_registry(self):
        self._registry_path = self.config.root_path / self.config.reg_file
        with open(self._registry_path, "r") as f:
            registry_data = yaml.safe_load(f)
        return registry_data

    # region Properties
    @property
    def file_name(self) -> str:
        """Gets the registry file name from the configuration."""
        return self._registry_path.name

    @property
    def reg_id(self) -> str:
        """Gets the registry ID from the loaded registry data."""
        if not self._reg_id:
            self._reg_id = self._reg.get("registry_id", "")
        return self._reg_id

    @property
    def reg_path(self) -> Path:
        """Gets the full path to the registry file."""
        return self._registry_path

    @property
    def reg_name(self) -> str:
        """Gets the registry name from the loaded registry data."""
        if not self._reg_name:
            self._reg_name = self._reg.get("registry_name", "")
        return self._reg_name

    @property
    def reg_version(self) -> str:
        """Gets the registry version from the loaded registry data."""
        if not self._reg_version:
            self._reg_version = self._reg.get("version", "")
        return self._reg_version

    @property
    def registry(self) -> dict:
        """Gets the entire registry data."""
        return self._reg

    # endregion Properties
