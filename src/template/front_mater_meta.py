from pathlib import Path
from typing import Any
from .front_matter_reader import FrontMatterReader


class FrontMatterMeta:
    def __init__(self, file_path: str | Path):
        self.file_path = file_path
        self.frontmatter, _ = FrontMatterReader().read_frontmatter(file_path)

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

        if self.frontmatter and field_name in self.frontmatter:
            return self.frontmatter[field_name]
        return default

    def has_field(self, field_name: str) -> bool:
        """Check if the instance's frontmatter contains a specific key."""
        return self.frontmatter is not None and field_name in self.frontmatter

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
            ['template_id', 'template_typeb']
        """

        if self.frontmatter:
            return sorted(self.frontmatter.keys())
        return []

    # region Properties
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

    # endregion Properties
