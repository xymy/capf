import abc
import os
import stat
from pathlib import Path
from typing import Protocol, TypeVar

T_co = TypeVar("T_co", covariant=True)


class Validator(Protocol[T_co]):
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


class PathValidator(Validator[Path]):
    def __init__(self, *, resolve: bool = False, exists: bool = False) -> None:
        self.resolve = resolve
        self.exists = exists

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
