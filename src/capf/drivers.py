import abc
import enum
from typing import TYPE_CHECKING, Generic, TypeVar

from .exceptions import CliMessage

if TYPE_CHECKING:
    from .validators import Validator

T = TypeVar("T")
S = TypeVar("S")


class ValueSource(enum.Enum):
    """The enumeration class for value sources.

    Attributes:
        DEFAULT: The value is from the default value.
        CLI: The value is from the command-line.
        ENV: The value is from the environment variable.
    """

    DEFAULT = 0
    CLI = 1
    ENV = 2


class Driver(metaclass=abc.ABCMeta):
    """The abstract base class for drivers.

    Args:
        num_values (int):
            The number of values :meth:`.__call__` can accept.
    """

    __slots__ = ("_count", "_value_source", "num_values")

    def __init__(self, *, num_values: int) -> None:
        self.num_values = num_values
        self._count = 0
        self._value_source = ValueSource.DEFAULT

    @property
    def count(self) -> int:
        """The number of times :meth:`.__call__` was called."""
        return self._count

    @property
    def present(self) -> bool:
        """Whether :meth:`.__call__` was called at least once.

        .. tip::

            You can use this to check whether any of associated arguments or
            options was present in the command-line.
        """
        return self._count > 0

    @abc.abstractmethod
    def __call__(self, values: list[str], *, source: ValueSource) -> None:
        """Parses the values and stores the result."""
        raise NotImplementedError


class ValueDriver(Driver, Generic[T, S]):
    __slots__ = ("validator", "value_parsed")

    def __init__(
        self, validator: "Validator[T]", *, default_value: S | None = None
    ) -> None:
        super().__init__(num_values=1)
        self.validator = validator
        self.value_parsed = default_value


class ScalarDriver(ValueDriver[T, T]):
    __slots__ = ()

    def __call__(self, values: list[str], *, source: ValueSource) -> None:
        assert len(values) == 1
        self.value_parsed = self.validator(values[0])
        self._count += 1
        self._value_source = source


class ListDriver(ValueDriver[T, list[T]]):
    __slots__ = ()

    def __call__(self, values: list[str], *, source: ValueSource) -> None:
        assert len(values) == 1
        if self.value_parsed is None or self._count == 0:
            self.value_parsed = []
        self.value_parsed.append(self.validator(values[0]))
        self._count += 1
        self._value_source = source


class FlagDriver(Driver, Generic[S]):
    __slots__ = ("value_parsed",)

    def __init__(self, *, default_value: S | None = None) -> None:
        super().__init__(num_values=0)
        self.value_parsed = default_value


class OnFlagDriver(FlagDriver):
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__(default_value=False)

    def __call__(self, values: list[str], *, source: ValueSource) -> None:
        assert len(values) == 0
        self.value_parsed = True
        self._count += 1
        self._value_source = source


class OffFlagDriver(FlagDriver):
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__(default_value=True)

    def __call__(self, values: list[str], *, source: ValueSource) -> None:
        assert len(values) == 0
        self.value_parsed = False
        self._count += 1
        self._value_source = source


class CountFlagDriver(FlagDriver[int]):
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__(default_value=0)

    def __call__(self, values: list[str], *, source: ValueSource) -> None:
        assert len(values) == 0
        if self.value_parsed is None or self._count == 0:
            self.value_parsed = 0
        self.value_parsed += 1
        self._count += 1
        self._value_source = source


class MessageDriver(FlagDriver):
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__()


class HelpDriver(MessageDriver):
    __slots__ = ()

    def __call__(self, values: list[str], *, source: ValueSource) -> None:
        assert len(values) == 0
        self._count += 1
        self._value_source = source
        raise CliMessage("help")


class VersionDriver(MessageDriver):
    __slots__ = ()

    def __call__(self, values: list[str], *, source: ValueSource) -> None:
        assert len(values) == 0
        self._count += 1
        self._value_source = source
        raise CliMessage("version")
