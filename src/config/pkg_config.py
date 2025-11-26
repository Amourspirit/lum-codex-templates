from typing import cast
from pathlib import Path
import toml
from ..meta.singleton import SingletonMeta


class PkgConfig(metaclass=SingletonMeta):
    def __init__(self):
        # store config_path as a string (used by _load_config)
        self._root_path = self._get_project_root()
        self._project_toml_path = self._root_path / "pyproject.toml"
        self._cfg = self._load_config()
        self._auto_invoke_scroll: str = ""
        self._base_file_count: int = -1
        self._batch_txt_protocol_src: str = ""
        self._bootstrap_src: str = ""
        self._current_user: str = ""
        self._files_upload_protocol_src: str = ""
        self._non_template_patterns: list[str] = []
        self._pkg_out_dir: str = ""
        self._protocol_src: str = ""
        self._readme_src: str = ""
        self._reg_file_name: str = ""
        self._reg_file: str = ""
        self._template_dirs: list[str] = []
        self._version_override: str = "NONE"
        self._version = ""

    def _load_config(self):
        return toml.load(self._project_toml_path)

    def _get_project_root(self) -> Path:
        # determine project root by looking from this files location and searching upwards
        current_path = Path(__file__).resolve()
        markers = (".git", "pyproject.toml", "uv.lock")
        for parent in (current_path.parent, *current_path.parents):
            if any((parent / m).exists() for m in markers):
                return parent
        return current_path.parent

    # region Properties
    @property
    def auto_invoke_scroll(self) -> str:
        """
        Return the cached auto invoke scroll string, loading it from configuration on first access.
        If self._auto_invoke_scroll is already set, that value is returned. Otherwise the method
        retrieves the value at self._cfg["tool"]["project"]["auto_invoke_scroll"], casts it to str, stores it
        in self._auto_invoke_scroll for future calls, and returns it.

        Returns:
            str: The auto invoke scroll value.
        """
        if not self._auto_invoke_scroll:
            self._auto_invoke_scroll = cast(
                str, self._cfg["tool"]["project"]["config"]["auto_invoke_scroll"]
            )
        return self._auto_invoke_scroll

    @property
    def base_file_count(self) -> int:
        """
        Return the cached base file count integer, loading it from configuration on first access.
        If self._base_file_count is already set, that value is returned. Otherwise the method
        retrieves the value at self._cfg["tool"]["project"]["base_file_count"], casts it to int, stores it
        in self._base_file_count for future calls, and returns it.

        Returns:
            int: The base file count value.
        """
        if self._base_file_count == -1:
            self._base_file_count = cast(
                int, self._cfg["tool"]["project"]["config"]["base_file_count"]
            )
        return self._base_file_count

    @property
    def batch_txt_protocol_src(self) -> str:
        """
        Return the cached batch text protocol source string, loading it from configuration on first access.
        If self._batch_txt_protocol_src is already set, that value is returned. Otherwise the method
        retrieves the value at self._cfg["tool"]["project"]["batch_txt_protocol_src"], casts it to str, stores it
        in self._batch_txt_protocol_src for future calls, and returns it.

        Returns:
            str: The batch text protocol source value.
        """
        if not self._batch_txt_protocol_src:
            self._batch_txt_protocol_src = cast(
                str,
                self._cfg["tool"]["project"]["config"]["batch_txt_protocol_src"],
            )
        return self._batch_txt_protocol_src

    @property
    def bootstrap_src(self) -> str:
        """
        Return the cached bootstrap source string, loading it from configuration on first access.
        If self._bootstrap_src is already set, that value is returned. Otherwise the method
        retrieves the value at self._cfg["project"]["bootstrap_src"], casts it to str, stores it
        in self._bootstrap_src for future calls, and returns it.

        Returns:
            str: The bootstrap source value.
        """
        if not self._bootstrap_src:
            self._bootstrap_src = cast(
                str, self._cfg["tool"]["project"]["config"]["bootstrap_src"]
            )
        return self._bootstrap_src

    @property
    def current_user(self) -> str:
        """
        Return the cached current user string, loading it from configuration on first access.
        If self._current_user is already set, that value is returned. Otherwise the method
        retrieves the value at self._cfg["tool"]["project"]["user"], casts it to str, stores it
        in self._current_user for future calls, and returns it.

        Returns:
            str: The current user value.
        """
        if not self._current_user:
            self._current_user = cast(
                str, self._cfg["tool"]["project"]["config"]["current_user"]
            )
        return self._current_user

    @property
    def files_upload_protocol_src(self) -> str:
        """
        Return the cached files upload protocol source string, loading it from configuration on first access.
        If self._files_upload_protocol_src is already set, that value is returned. Otherwise the method
        retrieves the value at self._cfg["tool"]["project"]["files_upload_protocol_src"], casts it to str, stores it
        in self._files_upload_protocol_src for future calls, and returns it.

        Returns:
            str: The files upload protocol source value.
        """
        if not self._files_upload_protocol_src:
            self._files_upload_protocol_src = cast(
                str, self._cfg["tool"]["project"]["config"]["files_upload_protocol_src"]
            )
        return self._files_upload_protocol_src

    @property
    def non_template_patterns(self) -> list[str]:
        """
        Return the cached non-template patterns list, loading it from configuration on first access.
        If self._non_template_patterns is already set, that value is returned. Otherwise the method
        retrieves the value at self._cfg["tool"]["project"]["non_template_patterns"], casts it to list[str], stores it
        in self._non_template_patterns for future calls, and returns it.

        Returns:
            list[str]: The non-template patterns value.
        """
        if not self._non_template_patterns:
            self._non_template_patterns = cast(
                list[str],
                self._cfg["tool"]["project"]["config"]["non_template_patterns"],
            )
        return self._non_template_patterns

    @property
    def pkg_out_dir(self) -> str:
        """
        Return the cached package output directory string, loading it from configuration on first access.
        If self._pkg_out_dir is already set, that value is returned. Otherwise the method
        retrieves the value at self._cfg["tool"]["project"]["pkg_out_dir"], casts it to str, stores it
        in self._pkg_out_dir for future calls, and returns it.

        Returns:
            str: The package output directory value.
        """
        if not self._pkg_out_dir:
            self._pkg_out_dir = cast(
                str, self._cfg["tool"]["project"]["config"]["pkg_out_dir"]
            )
        return self._pkg_out_dir

    @property
    def protocol_src(self) -> str:
        """
        Return the cached protocol source string, loading it from configuration on first access.
        If self._protocol_src is already set, that value is returned. Otherwise the method
        retrieves the value at self._cfg["tool"]["project"]["protocol_src"], casts it to str, stores it
        in self._protocol_src for future calls, and returns it.

        Returns:
            str: The protocol source value.
        """
        if not self._protocol_src:
            self._protocol_src = cast(
                str, self._cfg["tool"]["project"]["config"]["protocol_src"]
            )
        return self._protocol_src

    @property
    def readme_src(self) -> str:
        """
        Return the cached README source string, loading it from configuration on first access.
        If self._readme_src is already set, that value is returned. Otherwise the method
        retrieves the value at self._cfg["tool"]["project"]["readme_src"], casts it to str, stores it
        in self._readme_src for future calls, and returns it.

        Returns:
            str: The README source value.
        """
        if not self._readme_src:
            self._readme_src = cast(
                str, self._cfg["tool"]["project"]["config"]["readme_src"]
            )
        return self._readme_src

    @property
    def reg_file(self) -> str:
        """
        Return the cached registry file string, loading it from configuration on first access.
        If self._reg_file is already set, that value is returned. Otherwise the method
        retrieves the value at self._cfg["tool"]["project"]["reg_file"], casts it to str, stores it
        in self._reg_file for future calls, and returns it.

        Returns:
            str: The registry file value.
        """
        if not self._reg_file:
            self._reg_file = cast(
                str, self._cfg["tool"]["project"]["config"]["reg_file"]
            )
        return self._reg_file

    @property
    def reg_file_name(self) -> str:
        """
        Return the cached registry file name string, loading it from configuration on first access.
        If self._reg_file_name is already set, that value is returned. Otherwise the method
        retrieves the value at self._cfg["tool"]["project"]["reg_file_name"], casts it to str, stores it
        in self._reg_file_name for future calls, and returns it.

        Returns:
            str: The registry file name value.
        """
        if not self._reg_file_name:
            self._reg_file_name = cast(
                str, self._cfg["tool"]["project"]["config"]["reg_file_name"]
            )
        return self._reg_file_name

    @property
    def root_path(self) -> Path:
        """
        Return the root path of the project.

        Returns:
            Path: The root path of the project.
        """
        return self._root_path

    @property
    def template_dirs(self) -> list[str]:
        """
        Return the cached template directories list, loading it from configuration on first access.
        If self._template_dirs is already set, that value is returned. Otherwise the method
        retrieves the value at self._cfg["tool"]["project"]["template_dirs"], casts it to list[str], stores it
        in self._template_dirs for future calls, and returns it.

        Returns:
            list[str]: The template directories value.
        """
        if not self._template_dirs:
            self._template_dirs = cast(
                list[str], self._cfg["tool"]["project"]["config"]["template_dirs"]
            )
        return self._template_dirs

    @property
    def version_override(self) -> str:
        """
        Return the cached version override string, loading it from configuration on first access.
        If self._version_override is already set, that value is returned. Otherwise the method
        retrieves the value at self._cfg["tool"]["project"]["config"], casts it to str, stores it
        in self._version_override for future calls, and returns it.

        Returns:
            str: The version override value.

        Raises:
            KeyError: If the expected keys ("tool", "project", "config") are missing from self._cfg.
            TypeError: If the retrieved configuration value cannot be converted to a string.
        """

        if self._version_override == "NONE":
            self._version_override = cast(
                str, self._cfg["tool"]["project"]["config"]["version_override"]
            )
        else:
            self._version_override = ""
        return self._version_override

    @property
    def version(self) -> str:
        """
        Return the cached version string, loading it from configuration on first access.
        If self._version is already set, that value is returned. Otherwise the method
        retrieves the value at self._cfg["tool"]["project"]["version"], casts it to str, stores it
        in self._version for future calls, and returns it.

        Returns:
            str: The version value.
        """
        if not self._version:
            self._version = cast(str, self._cfg["project"]["version"])
        return self._version

    # endregion Properties
