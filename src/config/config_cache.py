from typing import TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    # avoid circular imports during runtime
    from .pkg_config import PkgConfig
else:
    PkgConfig = object


class ConfigCache:
    def __init__(self, config: PkgConfig):
        self._cache = {}
        self.config = config

    def get_api_path(self) -> Path:
        """Get the path to the API directory."""
        key = "api_path"
        if key not in self._cache:
            p = self.config.root_path / self.config.api_info.base_dir
            self._cache[key] = p
        return self._cache[key]

    def get_api_templates_path(self) -> Path:
        """Get the path to the API templates directory."""
        key = "api_templates_path"
        if key not in self._cache:
            p = (
                self.get_api_path()
                / self.config.api_info.info_templates.dir_name
                / "templates"
            )
            self._cache[key] = p
        return self._cache[key]

    def get_api_cbib_path(self) -> Path:
        """Get the path to the API templates cbib directory."""
        key = "api_cbib_path"
        if key not in self._cache:
            p = (
                self.get_api_path()
                / self.config.api_info.info_templates.dir_name
                / "executor_modes"
            )
            self._cache[key] = p
        return self._cache[key]

    def get_dist_single(self, build_number: int) -> Path:
        """Get the path to the single distribution directory for the given build number."""
        key = f"dist_single_{build_number}"
        if key not in self._cache:
            p = (
                self.config.root_path
                / self.config.pkg_out_dir
                / f"{build_number}-single"
            )
            self._cache[key] = p
        return self._cache[key]

    def get_dist_single_reports(self, build_number: int) -> Path:
        """Get the path to the single reports distribution directory for the given build number."""
        key = f"dist_single_reports_{build_number}"
        if key not in self._cache:
            p = (
                self.config.root_path
                / self.config.pkg_out_dir
                / f"{build_number}-{self.config.reports_dir}"
            )
            self._cache[key] = p
        return self._cache[key]

    def get_dist_single_cleaned(self, build_number: int) -> Path:
        """Get the path to the cleaned single distribution directory for the given build number."""
        key = f"dist_single_cleaned_{build_number}"
        if key not in self._cache:
            p = (
                self.config.root_path
                / self.config.pkg_out_dir
                / f"{build_number}-cleaned"
            )
            self._cache[key] = p
        return self._cache[key]

    def get_dist_single_upgrade(self, build_number: int) -> Path:
        """Get the path to the single upgrade distribution directory for the given build number."""
        key = f"dist_single_upgrade_{build_number}"
        if key not in self._cache:
            p = (
                self.config.root_path
                / self.config.pkg_out_dir
                / f"{build_number}-{self.config.upgrade_dir}"
            )
            self._cache[key] = p
        return self._cache[key]

    def clear_cache(self):
        self._cache.clear()
