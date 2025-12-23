from typing import Any

from .template_config_info import TemplateConfigInfo


class TemplatesConfigInfo:
    def __init__(self, templates_config: dict[str, Any]):
        """
        Initializes and validates the template configuration.

        Args:
            template_config: The dictionary from the TOML file corresponding to
                '[tool.project.templates]'.
        """
        self._tps_cfg = templates_config
        self._tci_items = {}
        if not isinstance(self._tps_cfg, dict) or not self._tps_cfg:
            raise ValueError("self._tps_cfg must be a non-empty dictionary.")

        template_types = sorted(list(self._tps_cfg.keys()))

        for template_type in template_types:
            template_info = self._tps_cfg[template_type]
            if not isinstance(template_info, dict):
                raise TypeError(
                    f"Template info for '{template_type}' must be a dictionary."
                )

            try:
                tci = TemplateConfigInfo(
                    template_id=template_info.get("id", ""),
                    template_name=template_info.get("name", ""),
                    template_category=template_info.get("category", ""),
                    template_version=template_info.get("version", ""),
                    template_family=template_info.get("family", ""),
                    template_type=template_info.get("template_type", ""),
                    expected_image=template_info.get("image_expected", False),
                    single_fields_omitted=set(
                        template_info.get("single_fields_omitted", [])
                    ),
                )
            except AssertionError as e:
                raise ValueError(
                    f"Validation error in template '{template_type}': {e}"
                ) from e

            # Store the validated TemplateConfigInfo back
            self._tci_items[template_type] = tci

    @property
    def tci_items(self) -> dict[str, TemplateConfigInfo]:
        return self._tci_items
