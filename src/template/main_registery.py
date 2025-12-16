from pathlib import Path
import yaml
from ..config.pkg_config import PkgConfig


class MainRegistry:
    def __init__(self, build_version: int):
        self.config = PkgConfig()
        self._reg: dict = self.load_registry()
        self._build_version = build_version
        self._reg_id = ""
        self._reg_version = ""
        self._reg_name = ""
        self._reg_ver_tuple = ()

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
            self._reg_version = ".".join(str(part) for part in self.reg_ver_tuple)
            # self._reg_version = self.reg_ver_tuple.__str__().replace("(", "").replace(")", "").replace(",", "").replace(" ", ".")
        return self._reg_version

    @property
    def reg_ver_tuple(self) -> tuple:
        """Gets the registry version as a tuple of integers."""
        if not self._reg_ver_tuple:
            version_str = self._reg.get("version", "0.0")
            version_parts = version_str.split(".")
            parts = list(int(part) for part in version_parts)
            while len(parts) < 3:
                parts.append(0)
            if len(parts) > 3:
                parts = parts[:3]
            parts[2] = self._build_version
            self._reg_ver_tuple = tuple(int(part) for part in parts)
        return self._reg_ver_tuple

    @property
    def registry(self) -> dict:
        """Gets the entire registry data."""
        return self._reg

    # endregion Properties
