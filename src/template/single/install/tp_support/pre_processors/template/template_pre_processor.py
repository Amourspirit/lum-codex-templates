from pathlib import Path

from src.template.front_mater_meta import FrontMatterMeta
from src.config.pkg_config import PkgConfig
from .protocol_template_pre_processor import ProtocolTemplatePreProcessor
from .pre_processor_dyad import PreProcessorDyad
from .pre_processor_field_cert_seal import PreProcessorFieldCertSeal
from .pre_processor_field_correction_scroll import PreProcessorFieldCorrectionScroll
from .pre_processor_field_certificate import PreProcessorFieldCertificate
from .pre_processor_glyph import PreProcessorGlyph
from .pre_processor_linkage_scroll import PreProcessorLinkageScroll
from .pre_processor_node_link_scroll import PreProcessorNodeLinkScroll
from .pre_processor_node_reg import PreProcessorNodeReg
from .pre_processor_seal import PreProcessorSeal
from .pre_processor_sigil import PreProcessorSigil
from .pre_processor_stone import PreProcessorStone


class TemplatePreProcessor:
    """
    Manages and executes a collection of ProtocolTemplatePreProcessor instances. Each process
    is responsible for processing a specific aspect of the package companions.

    Notes:
        - Writes templates into API subfolder.
        - Provides methods to register, unregister, and execute processes.
    """

    def __init__(
        self,
        templates_data: dict[str, FrontMatterMeta],
    ):
        self._config = PkgConfig()
        self._processes: list[ProtocolTemplatePreProcessor] = []
        self._templates_data = templates_data
        self._register_default_processes()

    def register_process(self, process: ProtocolTemplatePreProcessor) -> None:
        """Register a ProtocolTemplate with this processor.

        Args:
            process (ProtocolTemplate): The process instance to add to this processor. The object
                should implement the expected ProtocolTemplate interface.

        Returns:
            None
        """

        self._processes.append(process)

    def _get_base_path(self) -> Path:
        base_path = (
            self._config.root_path
            / self._config.api_info.base_dir
            / "lib"
            / "content_processors"
            / "pre_processors"
            / "templates"
        )
        return base_path

    def execute_single(self, template_type: str) -> tuple[str, Path]:
        """
        Execute a single registered process by template type and return its result path.
        Executes the first process found in self._processes matching the given template_type
        by calling its write_file() method and returns the returned Path object along with
        the template type.

        Args:
            template_type (str): The template type of the process to execute.
        Returns:
            tuple: A tuple containing the template type (str) and the Path object
                returned by the process's write_file() method.
        Raises:
            RuntimeError: If no processes are registered when this method is called.
            ValueError: If no process with the given template_type is found.
        """

        if not self._processes:
            raise RuntimeError(
                "No processes registered to execute. Has cleanup been called?"
            )
        base_path = self._get_base_path()
        base_path.mkdir(parents=True, exist_ok=True)
        base_init_file = base_path / "__init__.py"
        if not base_init_file.exists():
            with open(base_init_file, "w", encoding="utf-8") as f:
                pass
        for process in self._processes:
            if process.get_template_type() == template_type:
                fm = self._templates_data.get(process.get_template_type())
                if fm is None:
                    raise ValueError(
                        f"Template data for type '{process.get_template_type()}' not found."
                    )

                processor_path = (
                    base_path
                    / fm.template_type
                    / f"v{fm.template_version.replace('.', '_')}"
                )
                result_path = process.write_file(processor_path)
                init_file = processor_path / "__init__.py"
                if not init_file.exists():
                    with open(init_file, "w", encoding="utf-8") as f:  # noqa: F841
                        pass
                return (fm.template_type, result_path)
        raise ValueError(f"No process found for template type '{template_type}'.")

    def execute_all(self) -> dict[str, Path]:
        """
        Execute all registered processes and return their result paths.
        Executes each process registered in self._processes by calling its
        write_file() method and collects the returned Path objects keyed by the
        template type (as provided by process.get_template_type()).


        Returns:
            dict: A dictionary mapping template types (str) to the Path objects
                returned by each process's write_file() method.

        Raises:
            RuntimeError: If no processes are registered when this method is called.
            ValueError: If template data for a process's template type is not found
        """

        if not self._processes:
            raise RuntimeError(
                "No processes registered to execute. Has cleanup been called?"
            )
        results = {}
        base_path = self._get_base_path()
        base_path.mkdir(parents=True, exist_ok=True)
        base_init_file = base_path / "__init__.py"
        if not base_init_file.exists():
            with open(base_init_file, "w", encoding="utf-8") as f:
                pass
        for process in self._processes:
            fm = self._templates_data.get(process.get_template_type())
            if fm is None:
                raise ValueError(
                    f"Template data for type '{process.get_template_type()}' not found."
                )
            processor_path = (
                base_path
                / fm.template_type
                / f"v{fm.template_version.replace('.', '_')}"
            )
            result_path = process.write_file(processor_path)
            init_file = processor_path / "__init__.py"
            if not init_file.exists():
                with open(init_file, "w", encoding="utf-8") as f:  # noqa: F841
                    pass
            results[fm.template_type] = result_path
            print(
                f"Processed Template Pre-Processor: {fm.template_type} -> {result_path.name}"
            )
        return results

    def unregister_all(self) -> None:
        """Unregister all processes from the registry.
        Clears the internal _processes collection so that no previously
        registered processes are tracked by this processor. This operation
        is idempotent and returns None.

        Important:
        - This method only removes references from the registry and does not
            stop, terminate, or otherwise modify the underlying process objects.
        - If you need to perform cleanup or shutdown on the processes, do so
            before calling this method.
        - Callers should ensure proper synchronization if the registry may be
            accessed concurrently from multiple threads or tasks.
        Returns:
            None:
        """

        self._processes.clear()

    def unregister_process(self, process: ProtocolTemplatePreProcessor) -> None:
        """
        Unregister a process from the processor.
        Removes the first occurrence of the given process from the processor's internal list
        of registered processes.

        Args:
            process (ProtocolTemplate): The process instance to remove.

        Returns:
            None:

        Raises:
            ValueError: If the process is not currently registered.

        Notes:
            - Removal uses list.remove semantics, so equality (__eq__) is used to locate the
            process; identity is not guaranteed unless equality is identity-based.
            - This operation mutates the internal _processes list in place.
            - The method is not thread-safe; synchronize externally if concurrent access is possible.
        """

        self._processes.remove(process)

    def _register_default_processes(self) -> None:
        pp_dyad = PreProcessorDyad()
        self.register_process(pp_dyad)

        pp_field_cert_seal = PreProcessorFieldCertSeal()
        self.register_process(pp_field_cert_seal)

        pp_field_correction_scroll = PreProcessorFieldCorrectionScroll()
        self.register_process(pp_field_correction_scroll)

        pp_field_certificate = PreProcessorFieldCertificate()
        self.register_process(pp_field_certificate)

        pp_glyph = PreProcessorGlyph()
        self.register_process(pp_glyph)

        pp_linkage_scroll = PreProcessorLinkageScroll()
        self.register_process(pp_linkage_scroll)

        pp_node_link_scroll = PreProcessorNodeLinkScroll()
        self.register_process(pp_node_link_scroll)

        pp_node_reg = PreProcessorNodeReg()
        self.register_process(pp_node_reg)

        pp_seal = PreProcessorSeal()
        self.register_process(pp_seal)

        pp_sigil = PreProcessorSigil()
        self.register_process(pp_sigil)

        pp_stone = PreProcessorStone()
        self.register_process(pp_stone)

    @property
    def Count(self) -> int:
        """Get the count of registered processes.

        Returns:
            int: The number of processes currently registered in the processor.
        """

        return len(self._processes)
