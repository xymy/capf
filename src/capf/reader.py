from collections.abc import Sequence
from typing import Generic, TypeVar

T = TypeVar("T")


class Reader(Generic[T]):
    """Wrapper for stream reading with rollback.

    Args:
        tokens (collections.abc.Sequence[T]):
            The tokens to read.
        start (int | None, default=None):
            The start index of the tokens. If ``None``, ``0`` will be used.
        end (int | None, default=None):
            The end index of the tokens. If ``None``, ``len(tokens)`` will be
            used.
    """

    def __init__(
        self,
        tokens: Sequence[T],
        *,
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
        """Returns ``True`` if there is no more token."""
        return self._cursor == self.end

    def get(self) -> T:
        """Gets the current token and advances internal cursor."""
        if self._cursor == self.end:
            raise IndexError("index out of range")

        token = self.tokens[self._cursor]
        self._cursor += 1
        return token

    def put(self) -> None:
        """Advances internal cursor reversely."""
        if self._cursor == self.start:
            raise IndexError("index out of range")

        self._cursor -= 1
