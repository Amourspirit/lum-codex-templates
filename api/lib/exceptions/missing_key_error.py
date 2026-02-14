class MissingKeyError(Exception):
    """Custom exception for missing key errors."""

    def __init__(self, message: str, field_name: str, errors: list[str] | str) -> None:
        super().__init__(message)
        self.message = message
        self.field_name = field_name
        if isinstance(errors, str):
            self.errors = [errors]
        else:
            self.errors = errors

    def __str__(self) -> str:
        if self.errors:
            s = f"{self.message}\nErrors:\n"
            for err in self.errors:
                s += f" - {err}\n"
            return s
        return self.message
