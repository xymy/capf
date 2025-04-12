class CliSetupError(Exception):
    """Building command-line application fails."""


class CliParsingError(Exception):
    """Invalid command-line arguments are detected."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class CliMessage(Exception):
    """A message is emitted to the user."""

    def __init__(self, label: str, status: int = 0) -> None:
        super().__init__(label, status)
        self.label = label
        self.status = status
