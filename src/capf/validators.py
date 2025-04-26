import abc
import os
import stat
from collections.abc import Sequence
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Generic, TypeVar

T = TypeVar("T")


class Validator(Generic[T], metaclass=abc.ABCMeta):
    """The abstract base class for validators."""

    __slots__ = ()

    @abc.abstractmethod
    def __call__(self, value: str) -> T:
        """Converts string to desired type and checks whether it is a valid value."""
        raise NotImplementedError


class StrValidator(Validator[str]):
    """The default validator."""

    __slots__ = ()

    def __call__(self, value: str) -> str:
        return value


class BoolValidator(Validator[bool]):
    """The validator used to convert string to boolean.

    .. note::

        The following values will be recognized (case insensitive):

        - ``True``: ``"t"``, ``"true"``, ``"y"``, ``"yes"``, ``"on"``, ``"1"``.
        - ``False``: ``"f"``, ``"false"``, ``"n"``, ``"no"``, ``"off"``, ``"0"``.
    """

    __slots__ = ()

    def __call__(self, value: str) -> bool:
        value_lower = value.lower()
        if value_lower in {"t", "true", "y", "yes", "on", "1"}:
            return True
        if value_lower in {"f", "false", "n", "no", "off", "0"}:
            return False
        raise ValueError(f"{value!r} is not a valid boolean.")


class IntValidator(Validator[int]):
    """The validator used to convert string to integer.

    .. seealso::

        - https://docs.python.org/3/library/functions.html#int
    """

    __slots__ = ()

    def __call__(self, value: str) -> int:
        try:
            return int(value)
        except ValueError as e:
            raise ValueError(f"{value!r} is not a valid integer.") from e


class FloatValidator(Validator[float]):
    """The validator used to convert string to floating point number.

    .. seealso::

        - https://docs.python.org/3/library/functions.html#float
    """

    __slots__ = ()

    def __call__(self, value: str) -> float:
        try:
            return float(value)
        except ValueError as e:
            raise ValueError(
                f"{value!r} is not a valid floating point number."
            ) from e


class ChoiceValidator(Validator[T]):
    """The base class for choice validators.

    Args:
        validator (Validator[T]):
            The validator used to convert string to desired type.
        choices (collections.abc.Sequence[T]):
            The list of possible values.
    """

    __slots__ = ("choices", "validator")

    def __init__(self, validator: Validator[T], choices: Sequence[T]) -> None:
        super().__init__()
        if not choices:
            raise ValueError("choices must be non-empty.")
        self.validator = validator
        self.choices = list(choices)

    def __call__(self, value: str) -> T:
        value_parsed = self.validator(value)
        if value_parsed not in self.choices:
            raise ValueError(self._get_error_message(value))
        return value_parsed

    def _get_error_message(self, value: str) -> str:
        choices_str = ", ".join(map(repr, self.choices))
        if len(self.choices) < 2:
            return f"{value!r} is not {choices_str}."
        return f"{value!r} is not one of {choices_str}."


class StrChoiceValidator(ChoiceValidator[str]):
    """The validator used to check whether string is in a list.

    Args:
        choices (collections.abc.Sequence[str])
            The list of possible values.
        ignore_case (bool, default=False)
            Indicates whether to ignore case when checking the value.
        norm_case (bool, default=False)
            Indicates whether to return the normalized case of the value. That
            means, the value will be remapped to its equivalent in ``choices``.
            For example, if ``choices`` is ``["Android", "iOS"]`` and the value
            is ``"ios"``, the return value will be ``"iOS"``. This has no effect
            if ``ignore_case`` is ``False``.
    """

    __slots__ = ("ignore_case", "norm_case")

    def __init__(
        self,
        choices: Sequence[str],
        *,
        ignore_case: bool = False,
        norm_case: bool = False,
    ) -> None:
        super().__init__(StrValidator(), choices)
        self.ignore_case = ignore_case
        self.norm_case = norm_case

    def __call__(self, value: str) -> str:
        if not self.ignore_case:
            return super().__call__(value)

        value_parsed = self.validator(value)
        value_lower = value_parsed.lower()
        choices_lower = [choice.lower() for choice in self.choices]
        try:
            index = choices_lower.index(value_lower)
        except ValueError:
            raise ValueError(self._get_error_message(value)) from None
        return self.choices[index] if self.norm_case else value_parsed


class IntChoiceValidator(ChoiceValidator[int]):
    """The validator used to convert string to integer and check whether it is in a list.

    Args:
        choices (collections.abc.Sequence[int])
            The list of possible values.
    """

    __slots__ = ()

    def __init__(self, choices: Sequence[int]) -> None:
        super().__init__(IntValidator(), choices)


class FloatChoiceValidator(ChoiceValidator[float]):
    """The validator used to convert string to floating point number and check whether it is in a list.

    Args:
        choices (collections.abc.Sequence[float])
            The list of possible values.
    """

    __slots__ = ()

    def __init__(self, choices: Sequence[float]) -> None:
        super().__init__(FloatValidator(), choices)


class RangeValidator(Validator[T]):
    """The base class for range validators.

    Args:
        validator (Validator[T]):
            The validator used to convert string to desired type.
        min (T | None, default=None):
            The minimum value.
        max (T | None, default=None):
            The maximum value.
    """

    __slots__ = ("max", "min", "validator")

    def __init__(
        self,
        validator: Validator[T],
        min: T | None = None,
        max: T | None = None,
    ) -> None:
        super().__init__()
        if min is not None and max is not None and min > max:  # type: ignore [operator]
            raise ValueError("min must be less than or equal to max.")
        self.validator = validator
        self.min = min
        self.max = max

    def __call__(self, value: str) -> T:
        value_parsed = self.validator(value)
        if self.min is not None and value_parsed < self.min:  # type: ignore [operator]
            raise ValueError(
                f"{value!r} must be greater than or equal to {self.min!r}."
            )
        if self.max is not None and value_parsed > self.max:  # type: ignore [operator]
            raise ValueError(
                f"{value!r} must be less than or equal to {self.max!r}."
            )
        return value_parsed


class IntRangeValidator(RangeValidator[int]):
    """The validator used to convert string to integer and check whether it is in a range.

    Args:
        min (int | None, default=None)
            The minimum value.
        max (int | None, default=None)
            The maximum value.
    """

    __slots__ = ()

    def __init__(self, min: int | None = None, max: int | None = None) -> None:
        super().__init__(IntValidator(), min, max)


class FloatRangeValidator(RangeValidator[float]):
    """The validator used to convert string to floating point number and check whether it is in a range.

    Args:
        min (float | None, default=None)
            The minimum value.
        max (float | None, default=None)
            The maximum value.
    """

    __slots__ = ()

    def __init__(
        self, min: float | None = None, max: float | None = None
    ) -> None:
        super().__init__(FloatValidator(), min, max)


class DateTimeValidator(Validator[datetime]):
    """The validator used to convert string to date-time.

    Args:
        formats (Sequence[str] | None, default=None)
            The date-time formats used when parsing from string.

    .. note::

        By default, the following date-time formats will be recognized:

        - ``%Y-%m-%dT%H:%M:%S.%f%z`` (2025-01-01T20:00:00.000000+08:00)
        - ``%Y-%m-%dT%H:%M:%S.%f`` (2025-01-01T20:00:00.000000)
        - ``%Y-%m-%dT%H:%M:%S%z`` (2025-01-01T20:00:00+08:00)
        - ``%Y-%m-%dT%H:%M:%S`` (2025-01-01T20:00:00)
        - ``%Y-%m-%d`` (2025-01-01)

    .. seealso::

        - https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior
        - https://datatracker.ietf.org/doc/html/rfc3339
    """

    __slots__ = ("formats",)

    def __init__(self, formats: Sequence[str] | None = None) -> None:
        super().__init__()
        if formats is None:
            formats = [
                "%Y-%m-%dT%H:%M:%S.%f%z",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d",
            ]
        elif not formats:
            raise ValueError("formats must be non-empty.")
        self.formats = list(formats)

    def __call__(self, value: str) -> datetime:
        for format in self.formats:
            with suppress(ValueError):
                return datetime.strptime(value, format)
        raise ValueError(self._get_error_message(value))

    def _get_error_message(self, value: str) -> str:
        formats_str = ", ".join(map(repr, self.formats))
        if len(self.formats) < 2:
            return f"{value!r} does not match date-time format {formats_str}."
        return (
            f"{value!r} does not match any of date-time formats {formats_str}."
        )


class PathValidator(Validator[Path]):
    """The validator used to convert string to filesystem path.

    Args:
        resolve (bool, default=False)
            Indicates whether to resolve the path using
            :meth:`pathlib.Path.resolve`.
        exists (bool, default=False)
            Indicates whether to check the path exists.
        readable (bool, default=False)
            Indicates whether to check the path is readable.
        writable (bool, default=False)
            Indicates whether to check the path is writable.
        executable (bool, default=False)
            Indicates whether to check the path is executable.
    """

    __slots__ = ("executable", "exists", "readable", "resolve", "writable")

    def __init__(
        self,
        *,
        resolve: bool = False,
        exists: bool = False,
        readable: bool = False,
        writable: bool = False,
        executable: bool = False,
    ) -> None:
        super().__init__()
        self.resolve = resolve
        self.exists = exists
        self.readable = readable
        self.writable = writable
        self.executable = executable

    def __call__(self, value: str) -> Path:
        path = Path(value)
        if self.resolve:
            path = path.resolve()

        try:
            st = path.stat()
        except OSError as e:
            if not self.exists:
                return path
            raise ValueError(f"{str(path)!r} does not exist.") from e

        self._check_stat(path, st)
        if self.readable and not os.access(path, os.R_OK):
            raise ValueError(f"{str(path)!r} is not readable.")
        if self.writable and not os.access(path, os.W_OK):
            raise ValueError(f"{str(path)!r} is not writable.")
        if self.executable and not os.access(path, os.X_OK):
            raise ValueError(f"{str(path)!r} is not executable.")
        return path

    @staticmethod
    def _check_stat(path: Path, st: os.stat_result) -> None:
        pass


class DirPathValidator(PathValidator):
    """The validator used to convert string to filesystem path and check whether it is a directory."""

    __slots__ = ()

    @staticmethod
    def _check_stat(path: Path, st: os.stat_result) -> None:
        if not stat.S_ISDIR(st.st_mode):
            raise ValueError(f"{str(path)!r} is not a directory.")


class FilePathValidator(PathValidator):
    """The validator used to convert string to filesystem path and check whether it is a regular file."""

    __slots__ = ()

    @staticmethod
    def _check_stat(path: Path, st: os.stat_result) -> None:
        if not stat.S_ISREG(st.st_mode):
            raise ValueError(f"{str(path)!r} is not a file.")


def resolve_validator(validator: type | Validator | None) -> Validator:
    """Resolves common types to validators.

    +----------------------------+------------------------------+
    | Input                      | Output                       |
    +============================+==============================+
    | ``None``                   | :class:`StrValidator()`      |
    +----------------------------+------------------------------+
    | :class:`str`               | :class:`StrValidator()`      |
    +----------------------------+------------------------------+
    | :class:`bool`              | :class:`BoolValidator()`     |
    +----------------------------+------------------------------+
    | :class:`int`               | :class:`IntValidator()`      |
    +----------------------------+------------------------------+
    | :class:`float`             | :class:`FloatValidator()`    |
    +----------------------------+------------------------------+
    | :class:`datetime.datetime` | :class:`DateTimeValidator()` |
    +----------------------------+------------------------------+
    | :class:`pathlib.Path`      | :class:`PathValidator()`     |
    +----------------------------+------------------------------+
    """
    if isinstance(validator, Validator):
        return validator
    if validator is None or validator is str:
        return StrValidator()
    if validator is bool:
        return BoolValidator()
    if validator is int:
        return IntValidator()
    if validator is float:
        return FloatValidator()
    if validator is datetime:
        return DateTimeValidator()
    if validator is Path:
        return PathValidator()
    raise TypeError(f"Unsupported validator type: {validator!r}.")
