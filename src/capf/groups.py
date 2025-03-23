from collections.abc import Iterator
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from .core import Argument, Command, Option

T = TypeVar("T")


class Group(Generic[T]):
    """The generic group.

    Parameters
    ----------
    id : str
        The group id.
    title : str
        The group title. This will be displayed in the help information.
    """

    def __init__(self, id: str, title: str) -> None:
        self.id = id
        self.title = title
        self._members: list[T] = []

    def __bool__(self) -> bool:
        """Return ``True`` if this group has at least one member."""
        return bool(self._members)

    def __len__(self) -> int:
        """Return the number of members in this group."""
        return len(self._members)

    def __iter__(self) -> Iterator[T]:
        """Return an iterator of members in this group."""
        return iter(self._members)

    def add(self, member: T) -> None:
        """Add ``member`` to this group."""
        self._members.append(member)


class CommandGroup(Group["Command"]):
    """The group of commands.

    Parameters
    ----------
    id : str
        The group id.
    title : str
        The group title. This will be displayed in the help information.
    """


class ArgumentGroup(Group["Argument"]):
    """The group of arguments.

    Parameters
    ----------
    id : str
        The group id.
    title : str
        The group title. This will be displayed in the help information.
    """


class OptionGroup(Group["Option"]):
    """The group of options.

    Parameters
    ----------
    id : str
        The group id.
    title : str
        The group title. This will be displayed in the help information.
    multiple : bool, default=True
        If ``True``, allow more than one options in this group to be provided.
    required : bool, default=False
        If ``True``, require at least one option in this group to be provided.
    """

    def __init__(self, id: str, title: str, *, multiple: bool = True, required: bool = False) -> None:
        super().__init__(id, title)
        self.multiple = multiple
        self.required = required
