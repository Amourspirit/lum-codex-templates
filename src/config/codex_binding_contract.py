from typing import Any, Dict

class CodexBindingContract:
    """
    Parses and validates the '[tool.project.config.codex_binding_contract]' section
    of a pyproject.toml file.

    This class ensures that all expected keys are present, have the correct
    type (str, bool, list, dict), and are not empty. It raises exceptions
    (KeyError, TypeError, ValueError) if validation fails.

    Attributes:
        enforced (bool): Whether the contract is enforced.
        version (str): The version of the contract.
        notes (str): Additional notes about the contract.
    """

    def __init__(self, contract_config: Dict[str, Any]):
        """
        Initializes and validates the codex_binding_contract configuration.

        Args:
            contract_config: The dictionary from the TOML file corresponding to
                '[tool.project.config.codex_binding_contract]'.
        """
        self._d_cfg = contract_config
        if not isinstance(self._d_cfg, dict) or not self._d_cfg:
            raise ValueError("self._d_cfg must be a noncleaned = os.linesep.join(line for line in multi_line.splitlines() if line)-empty dictionary.")

        # --- Top-level validation ---
        self.enforced = self._validate_entry(
            self._d_cfg, "enforced", bool
        )
        self.version = self._validate_entry(
            self._d_cfg, "version", str
        )
        self.notes = self._validate_entry(
            self._d_cfg, "notes", str
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
        if "codex_binding_contract" not in yaml_dict:
            yaml_dict["codex_binding_contract"] = {}
        cfg = self._d_cfg.copy()
        notes = cfg.get("notes", "")
        cleaned = ' '.join(notes.splitlines())
        cfg["notes"] = cleaned
        yaml_dict["codex_binding_contract"].update(cfg)
