from collections.abc import Sequence


class Reader:
    """Wrapper for stream reading with rollback.

    Parameters
    ----------
    tokens : collections.abc.Sequence[str]
        The tokens to read.
    start : int | None, default=None
        The start index of the tokens. If ``None``, use ``0``.
    end : int | None, default=None
        The end index of the tokens. If ``None``, use ``len(tokens)``.
    """

    def __init__(
        self,
        tokens: Sequence[str],
        start: int | None = None,
        end: int | None = None,
    ) -> None:
        if start is None:
            start = 0
        elif start < 0:
            raise ValueError("invalid start index")

        if end is None:
            end = len(tokens)
        elif end > len(tokens):
            raise ValueError("invalid end index")

        if start > end:
            raise ValueError("invalid range")

        self.tokens = tokens
        self.start = start
        self.end = end
        self._cursor = start

    @property
    def cursor(self) -> int:
        """The current cursor."""
        return self._cursor

    def is_eof(self) -> bool:
        """Return ``True`` if there is no more token."""
        return self._cursor == self.end

    def get(self) -> str:
        """Get the current token and advance internal cursor."""
        if self._cursor == self.end:
            raise IndexError("index out of range")

        token = self.tokens[self._cursor]
        self._cursor += 1
        return token

    def put(self) -> None:
        """Reverse advance internal cursor."""
        if self._cursor == self.start:
            raise IndexError("index out of range")

        self._cursor -= 1
