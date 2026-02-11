from typing import Any
from src.template.front_mater_meta import FrontMatterMeta


class UpgradeTemplate:
    def __init__(
        self,
        upgrade_fm: FrontMatterMeta,
        template_fm: FrontMatterMeta,
    ):
        self._upgrade_fm = upgrade_fm
        self._template_fm = template_fm

    def _cleanup_content(self, content: str) -> str:
        """Cleanup content by removing extra new lines."""
        lines = content.splitlines()
        # replace all lines that are --- with * * *
        cleaned_lines = [line if line.strip() != "---" else "* * *" for line in lines]
        return "\n".join(cleaned_lines)

    def apply_upgrade(self) -> dict[str, Any]:
        new_fm = self._upgrade_fm.copy()
        new_fm.content = self._cleanup_content(new_fm.content)
        template_fields = set()
        for key, value in self._template_fm.frontmatter.items():
            template_fields.add(key)
            if key not in new_fm.frontmatter:
                new_fm.set_field(key, value)
        new_fm_fields = set(new_fm.frontmatter.keys())
        extra_fields = new_fm_fields - template_fields
        fields = set(
            [
                "template_category",
                "template_family",
                "template_filename",
                "template_hash",
                "template_name",
                "template_type",
                "template_version",
            ]
        )
        for field in fields:
            value = self._template_fm.get_field(field)
            new_fm.set_field(field, value)

        new_fm.template_version = self._template_fm.template_version.lstrip("v")
        new_fm.template_id = self._template_fm.template_id
        new_fm.recompute_sha256()

        return {
            "frontmatter": new_fm,
            "extra_fields": extra_fields,
        }
