from collections.abc import Sequence


class ReaderError(Exception):
    """Exception raised by :class:`Reader`."""


class Reader:
    """Wrapper for stream reading with rollback.

    Parameters
    ----------
    units : Sequence[str]
        Sequence of string unit to read.
    """

    def __init__(self, units: Sequence[str]) -> None:
        self.units = units
        self.index = 0

    def is_eof(self) -> bool:
        """Return ``True`` if there is no more unit."""
        return self.index >= len(self.units)

    def get(self) -> str:
        """Get the current unit and advance internal cursor."""
        if self.index >= len(self.units):
            raise ReaderError("index out of range")
        line = self.units[self.index]
        self.index += 1
        return line

    def put(self) -> None:
        """Reverse advance internal cursor."""
        if self.index == 0:
            raise ReaderError("index out of range")
        self.index -= 1
