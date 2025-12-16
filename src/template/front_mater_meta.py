from pathlib import Path
from typing import Any
from .obsidian_editor import ObsidianEditor
from ..config.pkg_config import PkgConfig
from ..util import sha


class FrontMatterMeta:
    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        self._frontmatter, self._content = ObsidianEditor().read_template(file_path)
        self.config = PkgConfig()
        self._sha256 = None
        if self._frontmatter is None:
            self._frontmatter = {}

    def get_field(self, field_name: str, default: Any = None) -> Any:
        """Retrieve a value from the object's frontmatter mapping.

        Args:
            field_name (str): The key to look up in `self.frontmatter`.
            default (Any, optional): Value to return if `self.frontmatter` is falsy
                or does not contain `field_name`. Defaults to None.

        Returns:
            Any: The value associated with `field_name` in `self.frontmatter` if
            present and `self.frontmatter` is truthy; otherwise `default`.

        Raises:
            None

        Notes:
            - Does not raise if `self.frontmatter` is missing or the key is absent;
            missing keys result in the `default` being returned.

        Examples:
            >>> self.frontmatter = {'title': 'Example'}
            >>> get_field('title')
            'Example'
            >>> get_field('author', 'Unknown')
            'Unknown'
        """

        if self._frontmatter and field_name in self._frontmatter:
            return self._frontmatter[field_name]
        return default

    def has_field(self, field_name: str) -> bool:
        """Check if the instance's frontmatter contains a specific key."""
        return self._frontmatter is not None and field_name in self._frontmatter

    def set_field(self, field_name: str, value: Any) -> None:
        """Set a value in the instance's frontmatter mapping.

        Args:
            field_name (str): The key to set in `self.frontmatter`.
            value (Any): The value to associate with `field_name`.
        """
        if self._frontmatter is None:
            self._frontmatter = {}
        self._frontmatter[field_name] = value

    def get_keys(self) -> list[str]:
        """Return a sorted list of keys from the instance's frontmatter.
        If the instance has a truthy mapping-like attribute `frontmatter` (for
        example, a dict), this method returns its keys as a list of strings
        sorted in ascending lexicographical order. If `frontmatter` is falsy or
        absent, an empty list is returned.
        Returns:
            list[str]: Sorted list of keys from `self.frontmatter`, or an empty
                list if no frontmatter is available.
        Example:
            >>> obj.frontmatter = {"template_type": "type_a", "template_id": "id_a}
            >>> obj.get_keys()
            ['template_id', 'template_type_b']
        """

        if self._frontmatter:
            return sorted(self._frontmatter.keys())
        return []

    def write_template(self, file_path: Path | str) -> Path:
        """
        Write the given frontmatter dict and content string to the specified file.
        The frontmatter is written as YAML fenced with '---' at the top of the file.

        Args:
            file_path (Path | str): The path to the file where the template will be written.
            frontmatter (dict): The frontmatter data to write as YAML.
            content (str): The markdown content to write after the frontmatter.

        Returns:
            Path: The path to the file that was written.
        """
        return ObsidianEditor().write_template(
            file_path, self.frontmatter, self.content
        )

    def _compute_sha256(self) -> str:
        """Compute and return the SHA-256 hash of the file at self.file_path."""
        fm = self.frontmatter.copy()
        _ = fm.pop(
            self.config.template_hash_field_name, None
        )  # Exclude existing sha256 field if present
        full_text = ObsidianEditor().get_template_str(fm, self.content)
        hash = sha.compute_str_sha256(full_text)
        self.frontmatter[self.config.template_hash_field_name] = hash
        return hash

    # region Properties
    @property
    def content(self) -> str:
        return self._content

    @content.setter
    def content(self, value: str) -> None:
        self._content = value

    @property
    def frontmatter(self) -> dict:
        return self._frontmatter  # type: ignore

    @property
    def template_id(self) -> str:
        return self.get_field("template_id", "")

    @property
    def template_version(self) -> str:
        return self.get_field("template_version", "")

    @property
    def template_type(self) -> str:
        return self.get_field("template_type", "")

    @property
    def template_category(self) -> str:
        return self.get_field("template_category", "")

    @property
    def template_name(self) -> str:
        return self.get_field("template_name", "")

    @property
    def template_origin(self) -> str:
        return self.get_field("template_origin", "")

    @property
    def declared_registry_id(self) -> str:
        return self.get_field("declared_registry_id", "")

    @declared_registry_id.setter
    def declared_registry_id(self, value: str) -> None:
        self.set_field("declared_registry_id", value)

    @property
    def declared_registry_version(self) -> str:
        return self.get_field("declared_registry_version", "")

    @declared_registry_version.setter
    def declared_registry_version(self, value: str) -> None:
        self.set_field("declared_registry_version", value)

    @property
    def mapped_registry(self) -> str:
        return self.get_field("mapped_registry", "")

    @mapped_registry.setter
    def mapped_registry(self, value: str) -> None:
        self.set_field("mapped_registry", value)

    @property
    def mapped_registry_minimum_version(self) -> str:
        return self.get_field("mapped_registry_minimum_version", "")

    @mapped_registry_minimum_version.setter
    def mapped_registry_minimum_version(self, value: str) -> None:
        self.set_field("mapped_registry_minimum_version", value)

    @property
    def sha256(self) -> str:
        """Compute and return the SHA-256 hash of the file at self.file_path."""
        if self._sha256 is None:
            self._sha256 = self._compute_sha256()
        return self._sha256

    # endregion Properties

    # region Static Methods
    @staticmethod
    def from_frontmatter_dict(
        file_path: str | Path, fm_dict: dict, content: str
    ) -> "FrontMatterMeta":
        """Create a FrontMatterMeta instance from a frontmatter dictionary.

        Args:
            file_path (str | Path): The path to the file associated with the frontmatter.
            fm_dict (dict): The frontmatter dictionary to use for initialization.
        Returns:
            FrontMatterMeta: An instance of FrontMatterMeta initialized with the
            provided frontmatter dictionary.
        """
        instance = FrontMatterMeta.__new__(FrontMatterMeta)
        instance._frontmatter = fm_dict
        instance._content = content
        if instance._frontmatter is None:
            instance._frontmatter = {}
        instance.file_path = file_path  # or set to a default value if needed
        instance._sha256 = None
        instance.config = PkgConfig()
        return instance

    # endregion Static Methods
