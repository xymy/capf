from collections.abc import Sequence


class Reader:
    """Wrapper for stream reading with rollback.

    Parameters
    ----------
    tokens : collections.abc.Sequence[str]
        The tokens to read.
    """

    def __init__(self, tokens: Sequence[str]) -> None:
        self._tokens = tokens
        self._cursor = 0

    def is_eof(self) -> bool:
        """Return ``True`` if there is no more token."""
        return self._cursor >= len(self._tokens)

    def get(self) -> str:
        """Get the current token and advance internal cursor."""
        if self._cursor >= len(self._tokens):
            raise IndexError("index out of range")
        token = self._tokens[self._cursor]
        self._cursor += 1
        return token

    def put(self) -> None:
        """Reverse advance internal cursor."""
        if self._cursor == 0:
            raise IndexError("index out of range")
        self._cursor -= 1
