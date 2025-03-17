class CliSetupError(Exception):
    """Raised when building command-line application fails."""


class CliParsingError(Exception):
    """Raised when invalid command-line arguments are detected."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class CliMessage(Exception):
    """Raised when a message is emitted to the user."""

    def __init__(self, label: str, status: int = 0) -> None:
        super().__init__(label, status)
        self.label = label
        self.status = status
