import abc
from typing import TYPE_CHECKING, Generic, TypeVar

from .exceptions import CliMessage

if TYPE_CHECKING:
    from .validators import Validator

T = TypeVar("T")
S = TypeVar("S")


class Adaptor(metaclass=abc.ABCMeta):
    """The abstract base class for adaptors."""

    __slots__ = ("count", "num_values")

    def __init__(self, *, num_values: int) -> None:
        self.num_values = num_values
        self.count = 0

    @abc.abstractmethod
    def __call__(self, values: list[str]) -> None:
        """Parse the values and store the result."""
        raise NotImplementedError


class ValueAdaptor(Adaptor, Generic[T, S]):
    __slots__ = ("validator", "value_parsed")

    def __init__(self, validator: "Validator[T]", *, default_value: S | None = None) -> None:
        super().__init__(num_values=1)
        self.validator = validator
        self.value_parsed = default_value


class ScalarAdaptor(ValueAdaptor[T, T]):
    __slots__ = ()

    def __call__(self, values: list[str]) -> None:
        assert len(values) == 1
        self.value_parsed = self.validator(values[0])
        self.count += 1


class ListAdaptor(ValueAdaptor[T, list[T]]):
    __slots__ = ()

    def __call__(self, values: list[str]) -> None:
        assert len(values) == 1
        if self.value_parsed is None or self.count == 0:
            self.value_parsed = []
        self.value_parsed.append(self.validator(values[0]))
        self.count += 1


class FlagAdaptor(Adaptor, Generic[S]):
    __slots__ = ("value_parsed",)

    def __init__(self, default_value: S | None = None) -> None:
        super().__init__(num_values=0)
        self.value_parsed = default_value


class OnFlagAdaptor(FlagAdaptor):
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__(default_value=False)

    def __call__(self, values: list[str]) -> None:
        assert len(values) == 0
        self.value_parsed = True
        self.count += 1


class OffFlagAdaptor(FlagAdaptor):
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__(default_value=True)

    def __call__(self, values: list[str]) -> None:
        assert len(values) == 0
        self.value_parsed = False
        self.count += 1


class MessageAdaptor(FlagAdaptor):
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__()


class HelpAdaptor(MessageAdaptor):
    __slots__ = ()

    def __call__(self, values: list[str]) -> None:
        assert len(values) == 0
        raise CliMessage("help")


class VersionAdaptor(MessageAdaptor):
    __slots__ = ()

    def __call__(self, values: list[str]) -> None:
        assert len(values) == 0
        raise CliMessage("version")
