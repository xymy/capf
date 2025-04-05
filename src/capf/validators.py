import abc
import os
import stat
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Generic, TypeVar

T_co = TypeVar("T_co", covariant=True)


class Validator(Generic[T_co], metaclass=abc.ABCMeta):
    """The abstract base class for validators."""

    __slots__ = ()

    @abc.abstractmethod
    def __call__(self, value: str) -> T_co:
        """Convert string to desired type and check whether it is a valid value."""
        raise NotImplementedError


class StrValidator(Validator[str]):
    """The default validator."""

    __slots__ = ()

    def __call__(self, value: str) -> str:
        return value


class BoolValidator(Validator[bool]):
    """The validator used to convert string to boolean."""

    __slots__ = ()

    def __call__(self, value: str) -> bool:
        value_lower = value.lower()
        if value_lower in {"t", "true", "y", "yes", "on", "1"}:
            return True
        if value_lower in {"f", "false", "n", "no", "off", "0"}:
            return False
        raise ValueError(f"{value!r} is not a valid boolean.")


class IntValidator(Validator[int]):
    """The validator used to convert string to integer."""

    __slots__ = ()

    def __call__(self, value: str) -> int:
        try:
            return int(value)
        except ValueError as e:
            raise ValueError(f"{value!r} is not a valid integer.") from e


class FloatValidator(Validator[float]):
    """The validator used to convert string to floating point number."""

    __slots__ = ()

    def __call__(self, value: str) -> float:
        try:
            return float(value)
        except ValueError as e:
            raise ValueError(f"{value!r} is not a valid floating point number.") from e


class ChoiceValidator(Validator[T_co]):
    """The base class for choice validators.

    Parameters
    ----------
    choices : collections.abc.Sequence[T_co]
        The list of possible values.
    validator : Validator[T_co]
        The validator used to convert string to desired type.
    """

    __slots__ = ("choices", "validator")

    def __init__(self, choices: Sequence[T_co], validator: Validator[T_co]) -> None:
        super().__init__()
        if not choices:
            raise ValueError("Empty choices is not allowed.")
        self.choices = list(choices)
        self.validator = validator

    def __call__(self, value: str) -> T_co:
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

    Parameters
    ----------
    choices : collections.abc.Sequence[str]
        The list of possible values.
    ignore_case : bool, default=False
        If ``True``, ignore case when checking the value.
    norm_case : bool, default=False
        If ``True``, return the normalized case of the value. That means, the value will be remapped to its equivalent
        in the ``choices``. For example, if the ``choices`` is ``["Android", "iOS"]`` and the value is ``"ios"``, the
        return value will be ``"iOS"``. This will take no effect if ``ignore_case`` is ``False``.
    """

    __slots__ = ("ignore_case", "norm_case")

    def __init__(self, choices: Sequence[str], *, ignore_case: bool = False, norm_case: bool = False) -> None:
        super().__init__(choices, StrValidator())
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

    Parameters
    ----------
    choices : collections.abc.Sequence[int]
        The list of possible values.
    """

    __slots__ = ()

    def __init__(self, choices: Sequence[int]) -> None:
        super().__init__(choices, IntValidator())


class FloatChoiceValidator(ChoiceValidator[float]):
    """The validator used to convert string to floating point number and check whether it is in a list.

    Parameters
    ----------
    choices : collections.abc.Sequence[float]
        The list of possible values.
    """

    __slots__ = ()

    def __init__(self, choices: Sequence[float]) -> None:
        super().__init__(choices, FloatValidator())


class DateTimeValidator(Validator[datetime]):
    """The validator used to convert string to date-time."""

    __slots__ = ()

    def __call__(self, value: str) -> datetime:
        try:
            return datetime.fromisoformat(value)
        except ValueError as e:
            raise ValueError(f"{value!r} is not a valid date-time.") from e


class PathValidator(Validator[Path]):
    """The validator used to convert string to filesystem path.

    Parameters
    ----------
    resolve : bool, default=False
        If ``True``, resolve the path using :meth:`pathlib.Path.resolve`.
    exists : bool, default=False
        If ``True``, check whether the path exists.
    readable : bool, default=False
        If ``True``, check whether the path is readable.
    writable : bool, default=False
        If ``True``, check whether the path is writable.
    executable : bool, default=False
        If ``True``, check whether the path is executable.
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


def resolve_validator(validator: type | Validator) -> Validator:
    """Resolve common types to validators.

    +----------------------------+------------------------------+
    | Input                      | Output                       |
    +============================+==============================+
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
    if validator is str:
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
