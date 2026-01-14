import importlib.util
from typing import Any
from src.config.pkg_config import PkgConfig
from ...util import camel_snake


class PreProcessRegistry:
    def __init__(self, registry: dict[str, Any], monad_name: str) -> None:
        self._monad_name = monad_name
        self._config = PkgConfig()
        self._registry = registry
        self._template_type: str = registry["template_type"]
        self._template_version: str = registry["template_version"]
        self._base_path = (
            self._config.root_path
            / self._config.api_info.base_dir
            / "lib"
            / "content_processors"
            / "pre_processors"
            / "templates"
        )

    def pre_process_registry(self) -> dict[str, Any]:
        pp_path = (
            self._base_path
            / self._template_type
            / f"v{self._template_version.replace('.', '_')}"
            / f"process_{self._template_type}_registry.py"
        )
        if not pp_path.exists():
            raise FileNotFoundError(f"Pre-processor file not found: {pp_path}")
        # import the pre-processor module dynamically

        spec = importlib.util.spec_from_file_location(
            f"process_{self._template_type}_registry", pp_path
        )
        assert spec is not None, f"Could not load spec for {pp_path}"
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None, f"Spec loader is None for {pp_path}"
        spec.loader.exec_module(module)  # type: ignore

        camel_name = camel_snake.to_camel_case(self._template_type)
        class_name = f"Process{camel_name}Registry"
        processor_class = getattr(module, class_name)
        processor_instance = processor_class(
            registry=self._registry, monad_name=self._monad_name
        )
        processed_reg = processor_instance.process()
        return processed_reg
