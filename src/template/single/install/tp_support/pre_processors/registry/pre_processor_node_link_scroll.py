from .protocol_template_pre_processor import ProtocolTemplatePreProcessor
from .template_base_pre_processor import TemplateBasePreProcessor


class PreProcessorNodeLinkScroll(
    TemplateBasePreProcessor, ProtocolTemplatePreProcessor
):
    def __init__(self) -> None:
        super().__init__()

    def get_template_type(self) -> str:
        """Return the type of the template being processed."""
        return "node_link_scroll"

    def _get_file_name(self) -> str:
        return "process_node_link_scroll_registry.py"

    def _get_content(self) -> str:
        return """from typing import Any, cast


class ProcessNodeLinkScrollRegistry:
    def __init__(self, *, registry: dict[str, Any], monad_name: str, **kwargs: Any):
        self.registry = registry.copy()
        self.monad_name = monad_name
        self._kwargs = kwargs

    def get_template_type(self) -> str:
        \"\"\"Return the type of the registry being processed.\"\"\"
        if "template_type" not in self.registry:
            raise ValueError("Registry must have a 'template_type' field.")
        tt = self.registry["template_type"]
        if not tt == "node_link_scroll":
            raise ValueError(
                f"Invalid template_type: {tt}. Expected 'node_link_scroll'."
            )
        return tt

    def _process_reg(self) -> None:
        if (
            "invocation_agents" in self.registry
            and "witness" in self.registry["invocation_agents"]
        ):
            self.registry["invocation_agents"]["witness"] = self.monad_name

        if (
            "autofill" in self.registry
            and "allowed_agents" in self.registry["autofill"]
        ):
            allowed_agents = cast(
                list[str], self.registry["autofill"]["allowed_agents"]
            )
            if self.monad_name not in allowed_agents:
                allowed_agents.append(self.monad_name)
                self.registry["autofill"]["allowed_agents"] = allowed_agents

    def process(self) -> dict[str, Any]:
        \"\"\"Main processing method to format the node_link_scroll registry.\"\"\"
        self._process_reg()
        return self.registry

"""
