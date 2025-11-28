import tempfile
from pathlib import Path
from .protocol_process import ProtocolProcess
from .process_readme import ProcessReadme
from .process_template_scroll import ProcessTemplateScroll
from ...main_registery import MainRegistry


class PkgCompanionsProcessor:
    def __init__(self, registry: MainRegistry):
        self._workspace_dir = Path(tempfile.mkdtemp(prefix="pkg_companions_"))
        self._main_registry = registry
        self._processes: list[ProtocolProcess] = []
        self._register_default_processes()

    def register_process(self, process: ProtocolProcess) -> None:
        self._processes.append(process)

    def execute_all(self, tokens: dict) -> dict[str, Path]:
        if not self._processes:
            raise RuntimeError(
                "No processes registered to execute. Has cleanup been called?"
            )
        results = {}
        for process in self._processes:
            result_path = process.process(tokens)
            results[process.get_process_name()] = result_path
        return results

    def unregister_all(self) -> None:
        self._processes.clear()

    def unregister_process(self, process: ProtocolProcess) -> None:
        self._processes.remove(process)

    def _register_default_processes(self) -> None:
        readme_processor = ProcessReadme(self._workspace_dir, self._main_registry)
        template_scroll_processor = ProcessTemplateScroll(
            self._workspace_dir, self._main_registry
        )
        self.register_process(readme_processor)
        self.register_process(template_scroll_processor)

    def cleanup(self) -> None:
        self.unregister_all()
        if self._workspace_dir.exists() and self._workspace_dir.is_dir():
            for item in self._workspace_dir.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    # Handle nested directories if needed
                    import shutil

                    shutil.rmtree(item)
            self._workspace_dir.rmdir()
