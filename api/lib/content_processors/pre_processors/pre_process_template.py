import importlib.util
from src.template.front_mater_meta import FrontMatterMeta
from src.config.pkg_config import PkgConfig
from ...util import camel_snake


class PreProcessTemplate:
    def __init__(self, template_content: str, monad_name: str) -> None:
        self._monad_name = monad_name
        self._config = PkgConfig()
        self._fm = FrontMatterMeta.from_content(template_content)
        self._base_path = (
            self._config.root_path
            / self._config.api_info.base_dir
            / "lib"
            / "content_processors"
            / "pre_processors"
            / "templates"
        )

    def pre_process_template(self) -> str:
        pp_path = (
            self._base_path
            / self._fm.template_type
            / f"v{self._fm.template_version.replace('.', '_')}"
            / f"process_{self._fm.template_type}_template.py"
        )
        if not pp_path.exists():
            raise FileNotFoundError(f"Pre-processor file not found: {pp_path}")
        # import the pre-processor module dynamically

        spec = importlib.util.spec_from_file_location(
            f"process_{self._fm.template_type}_template", pp_path
        )
        assert spec is not None, f"Could not load spec for {pp_path}"
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None, f"Spec loader is None for {pp_path}"
        spec.loader.exec_module(module)  # type: ignore

        camel_name = camel_snake.to_camel_case(self._fm.template_type)
        class_name = f"Process{camel_name}Template"
        processor_class = getattr(module, class_name)
        processor_instance = processor_class(
            template_content=self._fm.get_template_text(), monad_name=self._monad_name
        )
        processed_content = processor_instance.render()
        return processed_content
