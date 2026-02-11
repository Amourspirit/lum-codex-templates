from typing import Any

from src.template.front_mater_meta import FrontMatterMeta
from src.config.pkg_config import PkgConfig
from ..util.result import Result


class CleanMetaFields:
    def __init__(
        self,
        registry: dict[str, Any],
        fm: FrontMatterMeta,
    ):
        self.config = PkgConfig()

        self._registry = registry
        self._fm = fm

    def _get_filtered_fields(self, field_key: str) -> set[str]:
        found_fields: set[str] = set()
        fields: dict[str, dict[str, Any]] = self._registry.get("fields", {})
        for key, value in fields.items():
            field = value.get(field_key, None)
            if field is None:
                continue
            if field:
                found_fields.add(key)
        return found_fields

    def cleanup(self) -> FrontMatterMeta:
        hidden_fields = self._get_filtered_fields("hidden")
        fm = self._fm.copy()
        for field in hidden_fields:
            if fm.has_field(field):
                fm.remove_field(field)
        if not fm.template_id:
            fm.template_id = self._registry.get("template_id", "")
        return fm
