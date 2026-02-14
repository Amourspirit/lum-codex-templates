from pathlib import Path
from ....front_mater_meta import FrontMatterMeta
from ....main_registry import MainRegistry
from .protocol_template import ProtocolTemplate
from .template_dyad import TemplateDyad
from .template_field_cert_seal import TemplateFieldCertSeal
from .template_field_certificate import TemplateFieldCertificate
from .template_field_correction_scroll import TemplateFieldCorrectionScroll
from .template_general_scroll import TemplateGeneralScroll
from .template_glyph import TemplateGlyph
from .template_linkage_scroll import TemplateLinkageScroll
from .template_node_link_scroll import TemplateNodeLinkScroll
from .template_node_reg import TemplateNodeReg
from .template_seal import TemplateSeal
from .template_sigil import TemplateSigil
from .template_stone import TemplateStone


class TemplateProcessor:
    """
    Manages and executes a collection of ProtocolTemplate instances. Each process
    is responsible for processing a specific aspect of the package companions.

    Notes:
        - Writes template registry workspace directory.
        - Provides methods to register, unregister, and execute processes.
    """

    def __init__(
        self,
        workspace_dir: Path,
        registry: MainRegistry,
        templates_data: dict[str, FrontMatterMeta],
    ):
        self._workspace_dir = workspace_dir
        self._main_registry = registry
        self._processes: list[ProtocolTemplate] = []
        self._templates_data = templates_data
        self._register_default_processes()

    def register_process(self, process: ProtocolTemplate) -> None:
        """Register a ProtocolTemplate with this processor.

        Args:
            process (ProtocolTemplate): The process instance to add to this processor. The object
                should implement the expected ProtocolTemplate interface.

        Returns:
            None
        """

        self._processes.append(process)

    def execute_all(self, tokens: dict) -> dict[str, FrontMatterMeta]:
        """Execute all registered processes in sequence.

        Args:
            tokens (dict): A dictionary of tokens to pass to each process during execution.

        Returns:
            dict: A dictionary of dict[str, FrontMatterMeta] mapping template types to their processed
                FrontMatterMeta results.
        """

        if not self._processes:
            raise RuntimeError(
                "No processes registered to execute. Has cleanup been called?"
            )
        results = {}
        for process in self._processes:
            result_fm = process.process(tokens)
            results[result_fm.template_type] = result_fm
            print(
                f"Processed Template: {result_fm.template_type} -> {result_fm.file_path.name}"
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

    def unregister_process(self, process: ProtocolTemplate) -> None:
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
        template_glyph = TemplateGlyph(
            working_dir=self._workspace_dir,
            main_registry=self._main_registry,
            templates_data=self._templates_data,
        )
        self.register_process(template_glyph)
        template_field_certificate = TemplateFieldCertificate(
            working_dir=self._workspace_dir,
            main_registry=self._main_registry,
            templates_data=self._templates_data,
        )
        self.register_process(template_field_certificate)

        template_dyad = TemplateDyad(
            working_dir=self._workspace_dir,
            main_registry=self._main_registry,
            templates_data=self._templates_data,
        )
        self.register_process(template_dyad)

        template_stone = TemplateStone(
            working_dir=self._workspace_dir,
            main_registry=self._main_registry,
            templates_data=self._templates_data,
        )
        self.register_process(template_stone)

        template_node_reg = TemplateNodeReg(
            working_dir=self._workspace_dir,
            main_registry=self._main_registry,
            templates_data=self._templates_data,
        )
        self.register_process(template_node_reg)

        template_field_correction_scroll = TemplateFieldCorrectionScroll(
            working_dir=self._workspace_dir,
            main_registry=self._main_registry,
            templates_data=self._templates_data,
        )
        self.register_process(template_field_correction_scroll)

        template_linkage_scroll = TemplateLinkageScroll(
            working_dir=self._workspace_dir,
            main_registry=self._main_registry,
            templates_data=self._templates_data,
        )
        self.register_process(template_linkage_scroll)

        template_node_link_scroll = TemplateNodeLinkScroll(
            working_dir=self._workspace_dir,
            main_registry=self._main_registry,
            templates_data=self._templates_data,
        )
        self.register_process(template_node_link_scroll)

        template_field_cert_seal = TemplateFieldCertSeal(
            working_dir=self._workspace_dir,
            main_registry=self._main_registry,
            templates_data=self._templates_data,
        )
        self.register_process(template_field_cert_seal)

        template_seal = TemplateSeal(
            working_dir=self._workspace_dir,
            main_registry=self._main_registry,
            templates_data=self._templates_data,
        )
        self.register_process(template_seal)

        template_sigil = TemplateSigil(
            working_dir=self._workspace_dir,
            main_registry=self._main_registry,
            templates_data=self._templates_data,
        )
        self.register_process(template_sigil)

        template_general_scroll = TemplateGeneralScroll(
            working_dir=self._workspace_dir,
            main_registry=self._main_registry,
            templates_data=self._templates_data,
        )
        self.register_process(template_general_scroll)

    @property
    def Count(self) -> int:
        """Get the count of registered processes.

        Returns:
            int: The number of processes currently registered in the processor.
        """

        return len(self._processes)
