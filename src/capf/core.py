import sys
from collections.abc import Callable
from keyword import iskeyword
from typing import Any, NoReturn

import attrs

from capf.exceptions import CliMessage, CliParsingError, CliSetupError


def _check_dest(dest: str) -> None:
    if not dest.isidentifier():
        raise CliSetupError(f"Invalid dest: {dest!r} is not a valid identifier.")
    if iskeyword(dest):
        raise CliSetupError(f"Invalid dest: {dest!r} is a keyword.")


class Argument:
    def __init__(self, id: str, decl: str, *, dest: str = "", nvals: int = 1, required: bool = True) -> None:
        self.id = id
        self.argument = self._parse_decl(decl)
        self.dest = self._parse_dest(dest, self.id)
        self.nvals = self._parse_nvals(nvals)
        self.required = required

    @staticmethod
    def _parse_decl(decl: str) -> str:
        if not decl:
            raise CliSetupError("Invalid decl: Empty string is not allowed.")
        return decl

    @staticmethod
    def _parse_dest(dest: str, id: str) -> str:
        dest = dest or id
        _check_dest(dest)
        return dest

    @staticmethod
    def _parse_nvals(nvals: int) -> int:
        if nvals not in (1, -1, 0):
            raise CliSetupError("Invalid nvals: Value must be one of 1, -1 or 0.")
        return nvals


@attrs.define(kw_only=True)
class OptionElement:
    prefix: str
    text: str


class Option:
    def __init__(self, id: str, *decls: str, dest: str = "", nvals: int = 1, required: bool = False) -> None:
        self.id = id
        self.long_options, self.short_options = self._parse_decls(*decls)
        self.dest = self._parse_dest(dest, self.id)
        self.nvals = self._parse_nvals(nvals)
        self.required = required

    @staticmethod
    def _parse_decls(*decls: str) -> tuple[list[OptionElement], list[OptionElement]]:
        if not decls:
            raise CliSetupError("Invalid decls: At least one decl is required.")

        long_options: list[OptionElement] = []
        short_options: list[OptionElement] = []
        for decl in decls:
            if decl.startswith("--"):
                prefix, text = "--", decl[2:]
                if not text:
                    raise CliSetupError("Invalid decls: Empty string following prefix is not allowed.")
                if len(text) < 2:
                    raise CliSetupError(f"Invalid decls: Long option {decl!r} is too short.")
                long_options.append(OptionElement(prefix=prefix, text=text))
            elif decl.startswith("-"):
                prefix, text = "-", decl[1:]
                if not text:
                    raise CliSetupError("Invalid decls: Empty string following prefix is not allowed.")
                if len(text) > 1:
                    raise CliSetupError(f"Invalid decls: Short option {decl!r} is too long.")
                short_options.append(OptionElement(prefix=prefix, text=text))
            elif not decl:
                raise CliSetupError("Invalid decls: Empty string is not allowed.")
            else:
                raise CliSetupError(f"Invalid decls: {decl!r} does not start with prefix.")
        return long_options, short_options

    @staticmethod
    def _parse_dest(dest: str, id: str) -> str:
        dest = dest or id
        _check_dest(dest)
        return dest

    @staticmethod
    def _parse_nvals(nvals: int) -> int:
        if nvals not in (1, 0):
            raise CliSetupError("Invalid nvals: Value must be one of 1 or 0.")
        return nvals


class OptionGroup:
    def __init__(self, id: str, title: str) -> None:
        self.id = id
        self.title = title
        self.options: list[Option] = []

    def add(self, option: Option) -> None:
        self.options.append(option)


class Args:
    pass


class Command:
    def __init__(self, name: str, args: Any = None) -> None:
        self.name = name
        self.args = args if args is not None else Args()
        self.subcommands: list[Command] = []
        self.arguments: list[Argument] = []
        self.options: list[Option] = []
        self.option_groups: dict[str, OptionGroup] = {}
        self.callback = None

    @property
    def callback(self) -> Callable | None:
        return self._callback

    @callback.setter
    def callback(self, value: Callable | None) -> None:
        self._callback = value

    def add_argument(self, *args: Any, **kwargs: Any) -> Argument:
        argument = Argument(*args, **kwargs)
        self.arguments.append(argument)
        return argument

    def add_option(self, *args: Any, group_id: str = "", **kwargs: Any) -> Option:
        option = Option(*args, **kwargs)
        self.options.append(option)
        self._add_option_group(option, group_id)
        return option

    def _add_option_group(self, option: Option, group_id: str) -> None:
        if not group_id:
            if not self.option_groups:
                option_group = OptionGroup("options", "Options")
                self.option_groups["options"] = option_group
            else:
                option_group = list(self.option_groups.values())[-1]
        else:
            option_group = self.option_groups[group_id]
        option_group.add(option)


class Program:
    """The program.

    Parameters
    ----------
    name : str
        Name of this program. This will be displayed when user request to print version.
    version : str, default=""
        Version of this program. This will be displayed when user request to print version.
    exit_code_for_invalid_cli : int, default=2
        Exit code used for invalid CLI arguments.
    exit_code_for_unhandled_exception : int, default=2
        Exit code used for any other unhandled exception.
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
        self.exit_code_for_unhandled_exception = exit_code_for_unhandled_exception

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
