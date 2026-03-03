from enum import IntEnum


class SeverityKind(IntEnum):
    INFO = 10
    WARNING = 20
    ERROR = 30
    CRITICAL = 40

    def label(self) -> str:
        """
        Returns the lowercase string representation of the severity kind's name.
        This method converts the enum member's name to lowercase for use as a label.

        Returns:
            str: The lowercase name of the severity kind (e.g., 'info', 'warning', 'error').
        """

        return self.name.lower()
