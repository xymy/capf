import abc
import os
import stat
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Generic, TypeVar

T_co = TypeVar("T_co", covariant=True)


class Validator(Generic[T_co], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __call__(self, value: str) -> T_co:
        raise NotImplementedError


class StrValidator(Validator[str]):
    def __call__(self, value: str) -> str:
        return value


class BoolValidator(Validator[bool]):
    def __call__(self, value: str) -> bool:
        value_lower = value.lower()
        if value_lower in {"t", "true", "y", "yes", "on", "1"}:
            return True
        if value_lower in {"f", "false", "n", "no", "off", "0"}:
            return False
        raise ValueError(f"{value!r} is not a valid boolean.")


class IntValidator(Validator[int]):
    def __call__(self, value: str) -> int:
        try:
            return int(value)
        except ValueError as e:
            raise ValueError(f"{value!r} is not a valid integer.") from e


class FloatValidator(Validator[float]):
    def __call__(self, value: str) -> float:
        try:
            return float(value)
        except ValueError as e:
            raise ValueError(f"{value!r} is not a valid floating point number.") from e


class ChoiceValidator(Validator[T_co]):
    def __init__(self, choices: Sequence[T_co], validator: Validator[T_co]) -> None:
        if not choices:
            raise ValueError("Empty choices is not allowed.")
        self.choices = list(choices)
        self.validator = validator

    def __call__(self, value: str) -> T_co:
        value_validated = self.validator(value)
        if value_validated not in self.choices:
            raise ValueError(self._get_error_message(value))
        return value_validated

    def _get_error_message(self, value: str) -> str:
        choices_str = ", ".join(map(repr, self.choices))
        if len(self.choices) < 2:
            return f"{value!r} is not {choices_str}."
        return f"{value!r} is not one of {choices_str}."


class StrChoiceValidator(ChoiceValidator[str]):
    def __init__(self, choices: Sequence[str], *, ignore_case: bool = False, norm_case: bool = False) -> None:
        super().__init__(choices, StrValidator())
        self.ignore_case = ignore_case
        self.norm_case = norm_case

    def __call__(self, value: str) -> str:
        if not self.ignore_case:
            return super().__call__(value)

        value_lower = value.lower()
        choices_lower = [choice.lower() for choice in self.choices]
        try:
            index = choices_lower.index(value_lower)
        except ValueError as e:
            raise ValueError(self._get_error_message(value)) from e
        return self.choices[index] if self.norm_case else value


class IntChoiceValidator(ChoiceValidator[int]):
    def __init__(self, choices: Sequence[int]) -> None:
        super().__init__(choices, IntValidator())


class FloatChoiceValidator(ChoiceValidator[float]):
    def __init__(self, choices: Sequence[float]) -> None:
        super().__init__(choices, FloatValidator())


class DateTimeValidator(Validator[datetime]):
    def __call__(self, value: str) -> datetime:
        try:
            return datetime.fromisoformat(value)
        except ValueError as e:
            raise ValueError(f"{value!r} is not a valid datetime.") from e


class PathValidator(Validator[Path]):
    def __init__(
        self,
        *,
        resolve: bool = False,
        exists: bool = False,
        readable: bool = False,
        writable: bool = False,
        executable: bool = False,
    ) -> None:
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
    @staticmethod
    def _check_stat(path: Path, st: os.stat_result) -> None:
        if not stat.S_ISDIR(st.st_mode):
            raise ValueError(f"{str(path)!r} is not a directory.")


class FilePathValidator(PathValidator):
    @staticmethod
    def _check_stat(path: Path, st: os.stat_result) -> None:
        if not stat.S_ISREG(st.st_mode):
            raise ValueError(f"{str(path)!r} is not a file.")


def resolve_validator(validator: type | Validator) -> Validator:
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
