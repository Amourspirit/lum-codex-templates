from typing import Any, Dict


class TemplateConfig:
    """
    Parses and validates the '[tool.project.config.template]' section
    of a pyproject.toml file.

    This class ensures that all expected keys are present, have the correct
    type (str, bool, list, dict), and are not empty. It raises exceptions
    (KeyError, TypeError, ValueError) if validation fails.

    Attributes:
        field_placeholder_format (str): The format string for placeholders.
        placeholder_examples (List[str]): A list of example placeholders.
        placeholder (Dict[str, str]): Dictionary with 'open' and 'close' delimiters.
        prefix_semantics (Dict[str, Any]): Configuration for prefix semantics.
        placeholder_autofill_policy (Dict[str, str]): Policy for unresolved placeholders.
    """

    def __init__(self, template_config: Dict[str, Any]):
        """
        Initializes and validates the template configuration.

        Args:
            template_config: The dictionary from the TOML file corresponding to
                '[tool.project.config.template]'.
        """
        self._tp_cfg = template_config
        if not isinstance(self._tp_cfg, dict) or not self._tp_cfg:
            raise ValueError("self._tp_cfg must be a non-empty dictionary.")

        # --- Top-level validation ---
        self.field_placeholder_format = self._validate_entry(
            self._tp_cfg, "field_placeholder_format", str
        )
        self.placeholder_examples = self._validate_entry(
            self._tp_cfg, "placeholder_examples", list
        )

        # --- Nested Dictionaries Validation ---
        self.placeholder = self._validate_entry(
            self._tp_cfg, "field_placeholder_delimiters", dict
        )
        self._validate_entry(self.placeholder, "open", str)
        self._validate_entry(self.placeholder, "close", str)

        self.prefix_semantics = self._validate_entry(
            self._tp_cfg, "placeholder_prefix_semantics", dict
        )
        self._validate_entry(self.prefix_semantics, "required", bool)
        self._validate_entry(self.prefix_semantics, "allowed_prefixes", list)

        enforcement = self._validate_entry(self.prefix_semantics, "enforcement", dict)
        self._validate_entry(enforcement, "field", str)
        self._validate_entry(enforcement, "prompt", str)

        self.placeholder_autofill_policy = self._validate_entry(
            self._tp_cfg, "placeholder_autofill_policy", dict
        )
        self._validate_entry(self.placeholder_autofill_policy, "unresolved_field", dict)
        self._validate_entry(
            self.placeholder_autofill_policy, "unresolved_prompt", dict
        )
        # cleanup_fields are fields that can be removed from template metadata during cleanup
        cleanup_fields_single = self._validate_entry(
            self._tp_cfg, "cleanup_fields_single", list
        )
        self.cleanup_fields_single = set(cleanup_fields_single)

        cleanup_fields_zip = self._validate_entry(
            self._tp_cfg, "cleanup_fields_zip", list
        )
        self.cleanup_fields_zip = set(cleanup_fields_zip)

        apply_config_template_fields_signal = self._validate_entry(
            self._tp_cfg, "apply_config_template_fields_signal", list
        )
        self.apply_config_template_fields_signal = set(
            apply_config_template_fields_signal
        )

        apply_config_template_fields_zip = self._validate_entry(
            self._tp_cfg, "apply_config_template_fields_zip", list
        )
        self.apply_config_template_fields_zip = set(apply_config_template_fields_zip)

        api_installer_template_cleanup_fields = self._validate_entry(
            self._tp_cfg, "api_installer_template_cleanup_fields", list
        )
        self.api_installer_template_cleanup_fields = set(
            api_installer_template_cleanup_fields
        )

    def _validate_entry(self, config: dict, key: str, expected_type: type) -> Any:
        """
        Checks a key for existence, correct type, and non-empty value.
        Raises descriptive errors if checks fail.
        """
        if key not in config:
            raise KeyError(f"Missing required template config key: '{key}'")

        value = config[key]

        if not isinstance(value, expected_type):
            raise TypeError(
                f"Config key '{key}' has wrong type. "
                f"Expected {expected_type.__name__}, but got {type(value).__name__}."
            )

        # Booleans can be False, so we don't check them for emptiness.
        if expected_type in (str, list, dict):
            if not value:
                raise ValueError(f"Config key '{key}' must not be empty.")
            # Ensure all items in a list are non-empty strings
            if expected_type is list and not all(
                isinstance(i, str) and i for i in value
            ):
                raise ValueError(
                    f"All items in list '{key}' must be non-empty strings."
                )

        return value

    def update_yaml_dict(self, yaml_dict: dict) -> None:
        """
        Update a given YAML dictionary with template configuration values.

        Args:
            yaml_dict (dict): The YAML dictionary to update.
        """
        yaml_dict.update(self._tp_cfg)

    @property
    def tp_cfg(self) -> Dict[str, Any]:
        """Returns the raw template configuration dictionary."""
        return self._tp_cfg


# --- Example Usage ---
# import toml
#
# # Load the entire pyproject.toml file
# with open("pyproject.toml", "r") as f:
#     full_config = toml.load(f)
#
# # Extract the specific section for the template config
# template_data = full_config.get("tool", {}).get("project", {}).get("config", {}).get("template", {})
#
# try:
#     # Create an instance of the class
#     template_config = ConfigTemplate(template_data)
#
#     # Access validated configuration values
#     print(f"Placeholder open: {template_config.placeholder['open']}")
#     print(f"Allowed prefixes: {template_config.prefix_semantics['allowed_prefixes']}")
#
# except (KeyError, TypeError, ValueError) as e:
#     print(f"Configuration Error: {e}")
