import os
from typing import cast
from pathlib import Path
import toml
from ..meta.singleton import SingletonMeta
from .template_config import TemplateConfig
from .templates_config_info import TemplatesConfigInfo
from .codex_binding_contract import CodexBindingContract
from .template_cbib_info import TemplateCbibInfo
from .template_ceib_info import TemplateCeibInfo
from .api_info_templates import ApiInfoTemplates
from .api_info import ApiInfo
from .config_cache import ConfigCache


class PkgConfig(metaclass=SingletonMeta):
    def __init__(self):
        # store config_path as a string (used by _load_config)
        self._root_path = self._get_project_root()
        self._project_toml_path = self._root_path / "pyproject.toml"
        self._cfg = self._load_config()
        self._reg_file: str = ""

        # region read config values
        self._auto_invoke_scroll_name = cast(
            str, self._cfg["tool"]["project"]["config"]["auto_invoke_scroll_name"]
        )
        self._base_file_count: int = cast(
            int, self._cfg["tool"]["project"]["config"]["base_file_count"]
        )

        self._batch_txt_protocol_src = cast(
            str,
            self._cfg["tool"]["project"]["config"]["batch_txt_protocol_src"],
        )
        self._batch_prefix = cast(
            str,
            self._cfg["tool"]["project"]["config"]["batch_prefix"],
        )
        self._bootstrap_src = cast(
            str, self._cfg["tool"]["project"]["config"]["bootstrap_src"]
        )
        self._cleaned_dir = cast(
            str,
            self._cfg["tool"]["project"]["config"]["cleaned_dir"],
        )
        self._current_user = cast(
            str, self._cfg["tool"]["project"]["config"]["current_user"]
        )
        self._files_upload_protocol_src = cast(
            str, self._cfg["tool"]["project"]["config"]["files_upload_protocol_src"]
        )
        self._force_invalidate_previous = cast(
            bool, self._cfg["tool"]["project"]["config"]["force_invalidate_previous"]
        )
        self._lock_file_ext = cast(
            str, self._cfg["tool"]["project"]["config"]["lock_file_ext"]
        )
        self._lock_file_name = cast(
            str, self._cfg["tool"]["project"]["config"]["lock_file_name"]
        )

        # self._non_template_patterns = cast(
        #     list[str],
        #     self._cfg["tool"]["project"]["config"]["non_template_patterns"],
        # )
        self._package_output_name = cast(
            str, self._cfg["tool"]["project"]["config"]["package_output_name"]
        )
        self._pkg_out_dir = cast(
            str, self._cfg["tool"]["project"]["config"]["pkg_out_dir"]
        )
        self._protocol_src = cast(
            str, self._cfg["tool"]["project"]["config"]["protocol_src"]
        )
        self._readme_src = cast(
            str, self._cfg["tool"]["project"]["config"]["readme_src"]
        )
        self._reg_file = cast(str, self._cfg["tool"]["project"]["config"]["reg_file"])
        self._strict_field_mode = cast(
            bool, self._cfg["tool"]["project"]["config"]["strict_field_mode"]
        )
        self._reports_dir = cast(
            str, self._cfg["tool"]["project"]["config"]["reports_dir"]
        )
        self._strict_hash_mode = cast(
            bool, self._cfg["tool"]["project"]["config"]["strict_hash_mode"]
        )
        self._template_dirs = cast(
            list[str], self._cfg["tool"]["project"]["config"]["template_dirs"]
        )
        self._template_field_being_map_src = cast(
            str,
            self._cfg["tool"]["project"]["config"]["template_field_being_map_src"],
        )
        self._template_hash_field_name = cast(
            str,
            self._cfg["tool"]["project"]["config"]["template_hash_field_name"],
        )
        self._template_manifest_name = cast(
            str,
            self._cfg["tool"]["project"]["config"]["template_manifest_name"],
        )
        self._template_meta_dir = cast(
            str,
            self._cfg["tool"]["project"]["config"]["template_meta_dir"],
        )
        self._template_meta_keys = cast(
            set[str],
            set(self._cfg["tool"]["project"]["config"]["template_meta_keys"]),
        )
        self._template_to_field_being_map_name = cast(
            str,
            self._cfg["tool"]["project"]["config"]["template_to_field_being_map_name"],
        )
        self._template_to_field_being_upgrade_map_name = cast(
            str,
            self._cfg["tool"]["project"]["config"][
                "template_to_field_being_upgrade_map_name"
            ],
        )
        self._version_override = cast(
            int, self._cfg["tool"]["project"]["config"]["version_override"]
        )
        self._version = cast(str, self._cfg["project"]["version"])
        # endregion read config values

        self._upgrade_dir = cast(
            str,
            self._cfg["tool"]["project"]["config"]["upgrade_dir"],
        )

        self._validate_config()

        template_data = (
            self._cfg.get("tool", {})
            .get("project", {})
            .get("config", {})
            .get("template", {})
        )
        templates_info_data = (
            self._cfg.get("tool", {}).get("project", {}).get("templates", {})
        )
        self.templates_config_info = TemplatesConfigInfo(templates_info_data)

        contract_data = (
            self._cfg.get("tool", {})
            .get("project", {})
            .get("config", {})
            .get("codex_binding_contract", {})
        )
        self.template_config = TemplateConfig(template_data)
        self.codex_binding_contract = CodexBindingContract(contract_data)

        cbib_data = (
            self._cfg.get("tool", {})
            .get("project", {})
            .get("config", {})
            .get("template", {})
            .get("cbib", {})
        )
        self.template_cbib_single = TemplateCbibInfo(
            id=cbib_data.get("id", ""),
            title=cbib_data.get("title", ""),
            version=cbib_data["single"].get("version", ""),
            cbib_type="single",
        )

        self.template_cbib_zip = TemplateCbibInfo(
            id=cbib_data.get("id", ""),
            title=cbib_data.get("title", ""),
            version=cbib_data["zip"].get("version", ""),
            cbib_type="zip",
        )

        self.template_cbib_api = TemplateCbibInfo(
            id=cbib_data.get("id", ""),
            title=cbib_data.get("title", ""),
            version=cbib_data["api"].get("version", ""),
            cbib_type="api",
        )

        ceib_data = (
            self._cfg.get("tool", {})
            .get("project", {})
            .get("config", {})
            .get("template", {})
            .get("ceib", {})
        )
        self.template_ceib_single = TemplateCeibInfo(
            executor_mode=ceib_data.get("executor_mode", ""),
            title=ceib_data.get("title", ""),
            version=ceib_data["single"].get("version", ""),
        )

        self.template_ceib_zip = TemplateCeibInfo(
            executor_mode=ceib_data.get("executor_mode", ""),
            title=ceib_data.get("title", ""),
            version=ceib_data["zip"].get("version", ""),
        )

        self.template_ceib_api = TemplateCeibInfo(
            executor_mode=ceib_data.get("executor_mode", ""),
            title=ceib_data.get("title", ""),
            version=ceib_data["api"].get("version", ""),
        )

        self._env_user = self._get_env_user()

        # API INFO
        api_config_templates = (
            self._cfg.get("tool", {})
            .get("project", {})
            .get("config", {})
            .get("api", {})
            .get("templates", {})
        )
        api_info_templates = ApiInfoTemplates(
            dir_name=api_config_templates.get("dir_name", "")
        )

        api_info_data = (
            self._cfg.get("tool", {})
            .get("project", {})
            .get("config", {})
            .get("api", {})
        )
        self.api_info = ApiInfo(
            ttl_session_cache_seconds=api_info_data.get("ttl_session_cache_seconds", 0),
            info_templates=api_info_templates,
        )

        # Config Cache
        # must be last in init to ensure all config values are set
        self.config_cache = ConfigCache(self)

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

    def _validate_config(self):
        assert isinstance(self._auto_invoke_scroll_name, str), (
            "auto_invoke_scroll_name must be a string"
        )
        assert isinstance(self._base_file_count, int), (
            "base_file_count must be an integer"
        )
        assert self._base_file_count >= 0, "base_file_count must be non-negative"
        assert isinstance(self._batch_txt_protocol_src, str), (
            "batch_txt_protocol_src must be a string"
        )
        if self._batch_txt_protocol_src:
            batch_path = self._root_path / self._batch_txt_protocol_src
            assert batch_path.exists(), (
                f"batch_txt_protocol_src file does not exist: {batch_path}"
            )

        assert isinstance(self._batch_prefix, str), "batch_prefix must be a string"
        if not self._batch_prefix:
            raise ValueError("batch_prefix cannot be empty")

        assert isinstance(self._bootstrap_src, str), "bootstrap_src must be a string"
        if self._bootstrap_src:
            bootstrap_path = self._root_path / self._bootstrap_src
            assert bootstrap_path.exists(), (
                f"bootstrap_src file does not exist: {bootstrap_path}"
            )
        assert isinstance(self._cleaned_dir, str), "cleaned_dir must be a string"
        if not self._cleaned_dir:
            raise ValueError("cleaned_dir cannot be empty")
        assert isinstance(self._current_user, str), "current_user must be a string"
        if not self._current_user:
            raise ValueError("current_user cannot be empty")
        assert isinstance(self._files_upload_protocol_src, str), (
            "files_upload_protocol_src must be a string"
        )
        if self._files_upload_protocol_src:
            files_upload_path = self._root_path / self._files_upload_protocol_src
            assert files_upload_path.exists(), (
                f"files_upload_protocol_src file does not exist: {files_upload_path}"
            )
        assert isinstance(self._force_invalidate_previous, bool), (
            "force_invalidate_previous must be a boolean"
        )
        assert isinstance(self._lock_file_ext, str), "lock_file_ext must be a string"
        if not self._lock_file_ext.startswith("."):
            raise ValueError("lock_file_ext must start with a dot (.)")
        assert isinstance(self._lock_file_name, str), "lock_file_name must be a string"
        if not self._lock_file_name:
            raise ValueError("lock_file_name cannot be empty")

        # assert isinstance(self._non_template_patterns, list), (
        #     "non_template_patterns must be a list"
        # )
        # for pattern in self._non_template_patterns:
        #     assert isinstance(pattern, str), (
        #         "each item in non_template_patterns must be a string"
        #     )
        assert isinstance(self._package_output_name, str), (
            "package_output_name must be a string"
        )
        if not self._package_output_name:
            raise ValueError("package_output_name cannot be empty")
        assert isinstance(self._pkg_out_dir, str), "pkg_out_dir must be a string"
        assert isinstance(self._protocol_src, str), "protocol_src must be a string"
        if self._protocol_src:
            protocol_path = self._root_path / self._protocol_src
            assert protocol_path.exists(), (
                f"protocol_src file does not exist: {protocol_path}"
            )
        else:
            raise ValueError("protocol_src cannot be empty")
        assert isinstance(self._readme_src, str), "readme_src must be a string"
        if self._readme_src:
            readme_path = self._root_path / self._readme_src
            assert readme_path.exists(), (
                f"readme_src file does not exist: {readme_path}"
            )
        else:
            raise ValueError("readme_src cannot be empty")

        assert isinstance(self._reg_file, str), "reg_file must be a string"
        if self._reg_file:
            reg_path = self._root_path / self._reg_file
            assert reg_path.exists(), f"reg_file does not exist: {reg_path}"
        else:
            raise ValueError("reg_file cannot be empty")
        assert isinstance(self._reports_dir, str), "reports_dir must be a string"
        if not self._reports_dir:
            raise ValueError("reports_dir cannot be empty")
        assert isinstance(self._strict_field_mode, bool), (
            "strict_field_mode must be a boolean"
        )
        assert isinstance(self._strict_hash_mode, bool), (
            "strict_hash_mode must be a boolean"
        )
        assert isinstance(self._template_dirs, list), "template_dirs must be a list"
        for dir_name in self._template_dirs:
            assert isinstance(dir_name, str), (
                "each item in template_dirs must be a string"
            )
        assert isinstance(self._template_field_being_map_src, str), (
            "template_field_being_map_src must be a string"
        )
        if self._template_field_being_map_src:
            tfbm_path = self._root_path / self._template_field_being_map_src
            assert tfbm_path.exists(), (
                f"template_field_being_map_src file does not exist: {tfbm_path}"
            )
        assert isinstance(self._template_hash_field_name, str), (
            "template_hash_field_name must be a str"
        )
        if not self._template_hash_field_name:
            raise ValueError("template_hash_field_name cannot be empty")
        # assert that template_hash_field_name only has alphanumeric and underscores
        if not all(c.isalnum() or c == "_" for c in self._template_hash_field_name):
            raise ValueError(
                "template_hash_field_name must only contain alphanumeric characters and underscores"
            )
        assert isinstance(self._template_manifest_name, str), (
            "template_manifest_name must be a str"
        )
        if not self._template_manifest_name:
            raise ValueError("template_manifest_name cannot be empty")

        assert isinstance(self._template_meta_dir, str), (
            "template_meta_dir must be a str"
        )
        if not self._template_meta_dir:
            raise ValueError("template_meta_dir cannot be empty")

        template_meta_dir_path = self._root_path / self._template_meta_dir

        assert template_meta_dir_path.exists(), (
            f"template_meta_dir does not exist: {template_meta_dir_path}"
        )

        assert isinstance(self._template_meta_keys, set), (
            "template_meta_keys must be a set"
        )
        if not self._template_meta_keys:
            raise ValueError("template_meta_keys cannot be empty")
        for key in self._template_meta_keys:
            assert isinstance(key, str), (
                "each item in template_meta_keys must be a string"
            )

        assert isinstance(self._template_to_field_being_map_name, str), (
            "template_to_field_being_map_name must be a string"
        )

        if not self._template_to_field_being_map_name:
            raise ValueError("template_to_field_being_map_name cannot be empty")

        assert isinstance(self._template_to_field_being_upgrade_map_name, str)
        if not self._template_to_field_being_upgrade_map_name:
            raise ValueError("template_to_field_being_upgrade_map_name cannot be empty")

        assert isinstance(self._version_override, int), (
            "version_override must be an integer"
        )

        assert isinstance(self._version, str), "version must be a string"
        if not self._version:
            raise ValueError("version cannot be empty")

        assert isinstance(self._upgrade_dir, str), "upgrade_dir must be a string"
        if not self._upgrade_dir:
            raise ValueError("upgrade_dir cannot be empty")

    def _get_env_user(self) -> str:
        result = ""
        if os.getenv("CURRENT_USER") is None:
            result = self._current_user
        else:
            result = cast(str, os.getenv("CURRENT_USER"))
        return result

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
        return self._auto_invoke_scroll_name

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
        return self._batch_txt_protocol_src

    @property
    def batch_prefix(self) -> str:
        """
        Return the cached batch prefix string, loading it from configuration on first access.
        If self._batch_prefix is already set, that value is returned. Otherwise the method
        retrieves the value at self._cfg["tool"]["project"]["batch_prefix"], casts it to str, stores it
        in self._batch_prefix for future calls, and returns it.

        Returns:
            str: The batch prefix value.
        """
        return self._batch_prefix

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
        return self._bootstrap_src

    @property
    def cleaned_dir(self) -> str:
        """
        Return the cached cleaned directory string, loading it from configuration on first access.
        If self._cleaned_dir is already set, that value is returned. Otherwise the method
        retrieves the value at self._cfg["tool"]["project"]["cleaned_dir"], casts it to str, stores it
        in self._cleaned_dir for future calls, and returns it.

        Returns:
            str: The cleaned directory value.
        """
        return self._cleaned_dir

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
    def env_user(self) -> str:
        """
        Gets the current user from the environment variable or configuration.
        If the environment variable "CURRENT_USER" is set, its value is returned.
        Otherwise, the value from the configuration is returned.

        Returns:
            str: The user value.
        """
        return self._env_user

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
        return self._files_upload_protocol_src

    @property
    def force_invalidate_previous(self) -> bool:
        """
        Return the cached force invalidate previous boolean, loading it from configuration on first access.
        If self._force_invalidate_previous is already set, that value is returned. Otherwise the method
        retrieves the value at self._cfg["tool"]["project"]["force_invalidate_previous"], casts it to bool, stores it
        in self._force_invalidate_previous for future calls, and returns it.

        Returns:
            bool: The force invalidate previous value.
        """
        return self._force_invalidate_previous

    @property
    def lock_file_ext(self) -> str:
        """
        Return the cached lock file extension string, loading it from configuration on first access.
        If self._lock_file_ext is already set, that value is returned. Otherwise the method
        retrieves the value at self._cfg["tool"]["project"]["lock_file_ext"], casts it to str, stores it
        in self._lock_file_ext for future calls, and returns it.

        Returns:
            str: The lock file extension value.
        """
        return self._lock_file_ext

    @property
    def lock_file_name(self) -> str:
        """
        Return the cached lock file name string, loading it from configuration on first access.
        If self._lock_file_name is already set, that value is returned. Otherwise the method
        retrieves the value at self._cfg["tool"]["project"]["lock_file_name"], casts it to str, stores it
        in self._lock_file_name for future calls, and returns it.

        Returns:
            str: The lock file name value.
        """
        return self._lock_file_name

    # @property
    # def non_template_patterns(self) -> list[str]:
    #     """
    #     Return the cached non-template patterns list, loading it from configuration on first access.
    #     If self._non_template_patterns is already set, that value is returned. Otherwise the method
    #     retrieves the value at self._cfg["tool"]["project"]["non_template_patterns"], casts it to list[str], stores it
    #     in self._non_template_patterns for future calls, and returns it.

    #     Returns:
    #         list[str]: The non-template patterns value.
    #     """
    #     return self._non_template_patterns

    @property
    def package_output_name(self) -> str:
        """
        Return the cached package output name string, loading it from configuration on first access.
        If self._package_output_name is already set, that value is returned. Otherwise the method
        retrieves the value at self._cfg["tool"]["project"]["package_output_name"], casts it to str, stores it
        in self._package_output_name for future calls, and returns it.

        Returns:
            str: The package output name value.
        """
        return self._package_output_name

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
            reg_file_path = self._root_path / self._reg_file
            self._reg_file_name = reg_file_path.name
        return self._reg_file_name

    @property
    def reports_dir(self) -> str:
        """
        Return the cached reports directory string, loading it from configuration on first access.
        If self._reports_dir is already set, that value is returned. Otherwise the method
        retrieves the value at self._cfg["tool"]["project"]["reports_dir"], casts it to str, stores it
        in self._reports_dir for future calls, and returns it.

        Returns:
            str: The reports directory value.
        """
        return self._reports_dir

    @property
    def strict_field_mode(self) -> bool:
        """
        Return the cached strict field mode boolean, loading it from configuration on first access.
        If self._strict_field_mode is already set, that value is returned. Otherwise the method
        retrieves the value at self._cfg["tool"]["project"]["strict_field_mode"], casts it to bool, stores it
        in self._strict_field_mode for future calls, and returns it.

        Returns:
            bool: The strict field mode value.
        """
        return self._strict_field_mode

    @property
    def strict_hash_mode(self) -> bool:
        """
        Return the cached strict hash mode boolean, loading it from configuration on first access.
        If self._strict_hash_mode is already set, that value is returned. Otherwise the method
        retrieves the value at self._cfg["tool"]["project"]["strict_hash_mode"], casts it to bool, stores it
        in self._strict_hash_mode for future calls, and returns it.

        Returns:
            bool: The strict hash mode value.
        """
        return self._strict_hash_mode

    @property
    def root_path(self) -> Path:
        """
        Return the root path of the project.

        Returns:
            Path: The root path of the project.
        """
        return self._root_path

    @property
    def template_field_being_map_src(self) -> str:
        """
        Gets the source path for the template field being mapped.

        Returns:
            str: The source path for the template field being mapped.
        """
        return self._template_field_being_map_src

    @property
    def template_manifest_name(self) -> str:
        return self._template_manifest_name

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
    def template_hash_field_name(self) -> str:
        """
        Gets the template hash field name.

        Returns:
            str: The template hash field name.
        """
        return self._template_hash_field_name

    @property
    def template_meta_dir(self) -> str:
        """
        Gets the template meta directory.

        Returns:
            str: The template meta directory.
        """
        return self._template_meta_dir

    @property
    def template_meta_keys(self) -> set[str]:
        """
        Gets the template meta keys.

        Returns:
            set[str]: The template meta keys.
        """
        return self._template_meta_keys

    @property
    def template_to_field_being_map_name(self) -> str:
        """
        Gets the name for the template to field being map.

        Returns:
            str: The name for the template to field being map.
        """
        return self._template_to_field_being_map_name

    @property
    def template_to_field_being_upgrade_map_name(self) -> str:
        """
        Gets the name for the template to field being upgrade map.

        Returns:
            str: The name for the template to field being upgrade map.
        """
        return self._template_to_field_being_upgrade_map_name

    @property
    def version_override(self) -> int:
        """
        Return the version override string, loading it from configuration on first access.
        If self._version_override is already set, that value is returned. Otherwise the method
        retrieves the value at self._cfg["tool"]["project"]["config"], casts it to str, stores it
        in self._version_override for future calls, and returns it.

        Returns:
            int: The version override value.

        Raises:
            KeyError: If the expected keys ("tool", "project", "config") are missing from self._cfg.
            TypeError: If the retrieved configuration value cannot be converted to a string.
        """
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
        return self._version

    @property
    def upgrade_dir(self) -> str:
        """
        Gets the upgrade directory.

        Returns:
            str: The upgrade directory.
        """
        return self._upgrade_dir

    # endregion Properties
