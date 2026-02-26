from .protocol_template_pre_processor import ProtocolTemplatePreProcessor
from .template_base_pre_processor import TemplateBasePreProcessor


class PreProcessorFieldCertSeal(TemplateBasePreProcessor, ProtocolTemplatePreProcessor):
    def __init__(self) -> None:
        super().__init__()

    def get_template_type(self) -> str:
        """Return the type of the template being processed."""
        return "field_cert_seal"
