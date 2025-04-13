import sys
from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING, Any, Generic, NoReturn, TypeVar

from .exceptions import CliMessage, CliParsingError, CliSetupError

if TYPE_CHECKING:
    from .adaptors import Adaptor

T = TypeVar("T")


class Argument:
    def __init__(
        self,
        id: str,
        decl: str,
        *,
        adaptor: "Adaptor",
        multiple: bool = False,
        required: bool = True,
    ) -> None:
        self.id = id
        self.argument = self._parse_decl(decl)
        self.adaptor = adaptor
        self.multiple = multiple
        self.required = required

    @staticmethod
    def _parse_decl(decl: str) -> str:
        if not decl:
            raise CliSetupError("Invalid decl: Empty string is not allowed.")
        return decl


class Option:
    def __init__(
        self,
        id: str,
        *decls: str,
        adaptor: "Adaptor",
        multiple: bool = True,
        required: bool = False,
    ) -> None:
        self.id = id
        self.long_options, self.short_options = self._parse_decls(*decls)
        self.adaptor = adaptor
        self.multiple = multiple
        self.required = required

    @staticmethod
    def _parse_decls(*decls: str) -> tuple[list[str], list[str]]:
        if not decls:
            raise CliSetupError("Invalid decls: At least one decl is required.")

        long_options: list[str] = []
        short_options: list[str] = []
        for decl in decls:
            if decl.startswith("--"):
                text = decl[2:]
                if not text:
                    raise CliSetupError(
                        "Invalid decls: Empty string following prefix is not allowed."
                    )
                if len(text) < 2:
                    raise CliSetupError(
                        f"Invalid decls: Long option {decl!r} is too short."
                    )
                long_options.append(text)
            elif decl.startswith("-"):
                text = decl[1:]
                if not text:
                    raise CliSetupError(
                        "Invalid decls: Empty string following prefix is not allowed."
                    )
                if len(text) > 1:
                    raise CliSetupError(
                        f"Invalid decls: Short option {decl!r} is too long."
                    )
                short_options.append(text)
            elif not decl:
                raise CliSetupError(
                    "Invalid decls: Empty string is not allowed."
                )
            else:
                raise CliSetupError(
                    f"Invalid decls: {decl!r} does not start with prefix."
                )
        return long_options, short_options


class Group(Generic[T]):
    """The base class for groups.

    Args:
        id (str):
            The group id.
        title (str):
            The group title. This will be displayed in the help information.
    """

    def __init__(self, id: str, title: str) -> None:
        self.id = id
        self.title = title
        self._members: list[T] = []

    def __bool__(self) -> bool:
        """Returns ``True`` if this group has at least one member."""
        return bool(self._members)

    def __len__(self) -> int:
        """Returns the number of members in this group."""
        return len(self._members)

    def __iter__(self) -> Iterator[T]:
        """Returns an iterator of members in this group."""
        return iter(self._members)

    def add(self, member: T) -> None:
        """Adds a member to this group."""
        self._members.append(member)


class CommandGroup(Group["Command"]):
    """The group of commands.

    Args:
        id (str):
            The group id.
        title (str):
            The group title. This will be displayed in the help information.
    """


class ArgumentGroup(Group[Argument]):
    """The group of arguments.

    Args:
        id (str):
            The group id.
        title (str):
            The group title. This will be displayed in the help information.
    """


class OptionGroup(Group[Option]):
    """The group of options.

    Args:
        id (str):
            The group id.
        title (str):
            The group title. This will be displayed in the help information.
        multiple (bool, default=True):
            If ``True``, allow more than one options in this group to be provided.
        required (bool, default=False):
            If ``True``, require at least one option in this group to be provided.
    """

    def __init__(
        self,
        id: str,
        title: str,
        *,
        multiple: bool = True,
        required: bool = False,
    ) -> None:
        super().__init__(id, title)
        self.multiple = multiple
        self.required = required


class Command:
    def __init__(self, name: str) -> None:
        self.name = name
        self.command_groups: list[CommandGroup] = []
        self.argument_groups: list[ArgumentGroup] = []
        self.option_groups: list[OptionGroup] = []
        self.callback = None

    @property
    def callback(self) -> Callable | None:
        return self._callback

    @callback.setter
    def callback(self, value: Callable | None) -> None:
        self._callback = value

    def add_command(self, *args: Any, **kwargs: Any) -> "Command":
        command = Command(*args, **kwargs)
        if not self.command_groups:
            self.add_command_group("commands", "Commands")
        command_group = self.command_groups[-1]
        command_group.add(command)
        return command

    def add_command_group(self, id: str, title: str) -> CommandGroup:
        command_group = CommandGroup(id, title)
        self.command_groups.append(command_group)
        return command_group

    def add_argument(self, *args: Any, **kwargs: Any) -> Argument:
        argument = Argument(*args, **kwargs)
        if not self.argument_groups:
            self.add_argument_group("arguments", "Arguments")
        argument_group = self.argument_groups[-1]
        argument_group.add(argument)
        return argument

    def add_argument_group(self, id: str, title: str) -> ArgumentGroup:
        argument_group = ArgumentGroup(id, title)
        self.argument_groups.append(argument_group)
        return argument_group

    def add_option(self, *args: Any, **kwargs: Any) -> Option:
        option = Option(*args, **kwargs)
        if not self.option_groups:
            self.add_option_group("options", "Options")
        option_group = self.option_groups[-1]
        option_group.add(option)
        return option

    def add_option_group(
        self,
        id: str,
        title: str,
        *,
        multiple: bool = True,
        required: bool = False,
    ) -> OptionGroup:
        option_group = OptionGroup(
            id, title, multiple=multiple, required=required
        )
        self.option_groups.append(option_group)
        return option_group

    def is_leaf(self) -> bool:
        return not self.command_groups


class Program:
    """The program.

    Args:
        name (str):
            The name of this program. This will be displayed when the user
            request to print version.
        version (str, default=""):
            The version of this program. This will be displayed when the user
            request to print version.
        exit_code_for_invalid_cli (int, default=2):
            The exit code used for invalid CLI arguments.
        exit_code_for_unhandled_exception (int, default=2):
            The exit code used for any other unhandled exception.
    """

    def __init__(
        self,
        name: str,
        version: str = "",
        *,
        exit_code_for_invalid_cli: int = 2,
        exit_code_for_unhandled_exception: int = 2,
    ) -> None:
        self.name = name
        self.version = version

        self.exit_code_for_invalid_cli = exit_code_for_invalid_cli
        self.exit_code_for_unhandled_exception = (
            exit_code_for_unhandled_exception
        )

    def run(self, argv: list[str] | None = None) -> int:
        argv = self._resolve_argv(argv)

        return 0

    def run_and_exit(self, argv: list[str] | None = None) -> NoReturn:
        argv = self._resolve_argv(argv)

        try:
            sys.exit(self.run(argv))
        except CliMessage as e:
            sys.exit(e.status)
        except CliParsingError as e:
            from rich.console import Console

            console = Console(stderr=True)
            console.print(e.message)
            sys.exit(self.exit_code_for_invalid_cli)
        except Exception:  # noqa: BLE001
            from rich.console import Console

            console = Console(stderr=True)
            console.print_exception()
            sys.exit(self.exit_code_for_unhandled_exception)

    @staticmethod
    def _resolve_argv(argv: list[str] | None) -> list[str]:
        if argv is None:
            return sys.argv
        if not argv:
            raise CliSetupError(
                "Invalid argv: Empty list is not allowed. It must contain at least one item for program name."
            )
        return argv
