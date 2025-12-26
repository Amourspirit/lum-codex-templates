from contextlib import suppress
from ..config.pkg_config import PkgConfig


class BuildVerMgr:
    def __init__(self, initial_version: int = 0):
        self.version = initial_version
        self._config = PkgConfig()
        self._storage_name = ".mkpkg_last"

    def get_saved_version(self) -> int:
        """
        Return the saved integer version stored in the configured storage file.

        Returns:
            int: Parsed version number from the storage file, or 0 if unavailable or invalid.
        """

        version = 0
        with suppress(Exception):
            storage_path = self._config.root_path / self._storage_name
            if storage_path.exists():
                with open(storage_path, "r") as f:
                    last_version_str = f.read().strip()
                    if last_version_str.isdigit():
                        version = int(last_version_str)

        return version

    def get_next_version(self) -> int:
        """
        Retrieves the next version number by incrementing the saved version by 1.
        If an exception occurs during the retrieval, returns the current version.

        Returns:
            int: The next version number.
        """

        with suppress(Exception):
            self.version = self.get_saved_version() + 1

        return self.version

    def save_current_version(self) -> None:
        """
        Saves the current version to a storage file.
        This method writes the string representation of the current version to a file
        located at the storage path derived from the configuration. If an exception
        occurs during the process, it is suppressed and the method returns silently.

        Returns:
            None:
        """

        with suppress(Exception):
            storage_path = self._config.root_path / self._storage_name
            with open(storage_path, "w") as f:
                f.write(str(self.version))
