from typing import Any, cast


class ProcessSealRegistry:
    def __init__(self, *, registry: dict[str, Any], monad_name: str, **kwargs: Any):
        self.registry = registry.copy()
        self.monad_name = monad_name
        self._kwargs = kwargs

    def get_template_type(self) -> str:
        """Return the type of the registry being processed."""
        if "template_type" not in self.registry:
            raise ValueError("Registry must have a 'template_type' field.")
        tt = self.registry["template_type"]
        if not tt == "seal":
            raise ValueError(f"Invalid template_type: {tt}. Expected 'seal'.")
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
        """Main processing method to format the seal registry."""
        self._process_reg()
        return self.registry

