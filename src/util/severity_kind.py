from enum import Enum


class SeverityKind(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
