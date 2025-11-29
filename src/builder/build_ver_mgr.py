from ..config.pkg_config import PkgConfig


class BuildVerMgr:
    def __init__(self, initial_version: int = 0):
        self.version = initial_version
        self._config = PkgConfig()
        self._storage_name = ".mkpkg_last"

    def get_next_version(self) -> int:
        try:
            storage_path = self._config.root_path / self._storage_name
            if storage_path.exists():
                with open(storage_path, "r") as f:
                    last_version_str = f.read().strip()
                    if last_version_str.isdigit():
                        self.version = int(last_version_str) + 1
        except Exception:
            pass  # If any error occurs, just return the current version

        return self.version

    def save_current_version(self) -> None:
        try:
            storage_path = self._config.root_path / self._storage_name
            with open(storage_path, "w") as f:
                f.write(str(self.version))
        except Exception:
            pass  # Ignore errors during saving
