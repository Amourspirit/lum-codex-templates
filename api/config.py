from pathlib import Path
from dataclasses import dataclass
import json


class ConfigMeta(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        # If arguments are provided, create a new instance normally
        if args or kwargs:
            return super().__call__(*args, **kwargs)

        # Singleton behavior for no arguments
        if cls._instance is None:
            root = Path(__file__).parent
            config_file = Path(root, "config.json")
            if config_file.exists():
                with open(config_file, "r") as file:
                    data = json.load(file)
            else:
                # Provide default values if config.json doesn't exist
                data = {
                    "current_api_prefix": "/api/v1",
                    "api_v1_prefix": "/api/v1",
                    "templates_mcp_path": "/templates/mcp",
                }
            cls._instance = super().__call__(**data)
        return cls._instance


@dataclass(frozen=True)
class Config(metaclass=ConfigMeta):
    """
    Singleton Configuration Class

    Generally speaking this class is only used internally.
    """

    current_api_prefix: str = ""
    """
    Current API prefix such as ``/api/v1``
    """
    api_v1_prefix: str = ""
    """
    API v1 prefix such as ``/api/v1``
    """

    templates_mcp_path: str = ""
    """
    Path for the templates MCP such as ``/templates/mcp``
    """


cfg = Config()
