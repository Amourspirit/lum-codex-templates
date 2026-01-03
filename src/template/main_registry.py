from pathlib import Path
from typing import Any
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

    def get_field_py_type(self, field_name: str) -> tuple[type, str] | None:
        """
        Retrieves the Python type and an optional subtype string for a given field name.
        This method looks up the field in the metadata_fields dictionary. If the field exists
        and has a "type" key, it maps the type string to a corresponding Python type and
        subtype (if applicable) using a predefined type mapping. Supported types include
        basic types like str, int, bool, float, list, dict, and lists of those types.

        Args:
            field_name (str): The name of the field to retrieve the type for.

        Returns:
            tuple[type, str] | None: A tuple containing the Python type and a subtype string
            (which may be empty), or None if the field does not exist or has no type defined.
        """

        metadata_fields = self.metadata_fields
        field_info = metadata_fields.get(field_name)
        if not field_info:
            return None
        field_type_str = field_info.get("field_type")
        if not field_type_str:
            return None
        type_mapping = {
            "string": (str, ""),
            "integer": (int, ""),
            "boolean": (bool, ""),
            "str": (str, ""),
            "int": (int, ""),
            "bool": (bool, ""),
            "float": (float, ""),
            "number": (float, ""),
            "num": (float, ""),
            "list": (list, ""),
            "dict": (dict, ""),
            "object": (dict, ""),
            "list[string]": (list, "str"),
            "list[integer]": (list, "int"),
            "list[boolean]": (list, "bool"),
            "list[float]": (list, "float"),
            "list[str]": (list, "str"),
            "list[int]": (list, "int"),
            "list[bool]": (list, "bool"),
        }
        return type_mapping.get(field_type_str.lower())

    # region Properties
    @property
    def build_version(self) -> int:
        """Gets the build version."""
        return self._build_version

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

    @property
    def metadata_fields(self) -> dict[str, dict[str, Any]]:
        """Gets the metadata fields from the registry data."""
        return self._reg.get("metadata_fields", {})

    # endregion Properties
