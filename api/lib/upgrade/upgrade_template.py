from typing import Any
from src.template.front_mater_meta import FrontMatterMeta
from .rules.upgrade_engine import create_default_upgrade_engine
from .exceptions import UpgradeError


class UpgradeTemplate:
    def __init__(
        self,
        upgrade_fm: FrontMatterMeta,
        template_fm: FrontMatterMeta,
        registry: dict[str, Any],
    ):
        self._upgrade_fm = upgrade_fm
        self._template_fm = template_fm
        self._registry = registry

    def apply_upgrade(self) -> dict[str, Any]:

        engine = create_default_upgrade_engine()
        summary = engine.apply(self._upgrade_fm, self._template_fm, self._registry)
        if summary.errors:
            errors_list: set[str] = set()
            for name, errors in summary.errors.items():
                for err in errors:
                    errors_list.add(f"Name '{name}': {str(err)}")
            raise UpgradeError(
                "Upgrade failed with errors",
                "field_errors",
                errors=list(errors_list),
            )

        new_fm = summary.artifact
        template_fields = set(self._template_fm.frontmatter.keys())

        new_fm_fields = set(new_fm.frontmatter.keys())
        extra_fields = new_fm_fields - template_fields

        return {
            "frontmatter": new_fm,
            "extra_fields": extra_fields,
            "warnings": summary.warnings,
            "logs": summary.logs,
        }
