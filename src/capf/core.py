import sys
from collections.abc import Callable, Sequence
from keyword import iskeyword
from typing import Any

import attrs


class CapfError(Exception):
    pass


def _check_dest(dest: str) -> None:
    if not dest.isidentifier():
        raise CapfError(f"Invalid dest: {dest!r} is not a valid identifier.")
    if iskeyword(dest):
        raise CapfError(f"Invalid dest: {dest!r} is a keyword.")


class Argument:
    def __init__(self, decl: str, *, dest: str = "", nvals: int = 1, required: bool = True) -> None:
        self.argument = self._parse_decl(decl)
        self.dest = self._parse_dest(dest, self.argument)
        self.nvals = nvals
        self.required = required

    @staticmethod
    def _parse_decl(decl: str) -> str:
        if not decl:
            raise CapfError("Invalid decl: Empty string is not allowed.")
        return decl

    @staticmethod
    def _parse_dest(dest: str, argument: str) -> str:
        real_dest = dest or argument
        real_dest = real_dest.replace("-", "_")
        _check_dest(real_dest)
        return real_dest


@attrs.define(kw_only=True)
class OptionElement:
    prefix: str
    text: str


class Option:
    def __init__(self, *decls: str, dest: str = "", nvals: int = 1, required: bool = False) -> None:
        self.long_options, self.short_options = self._parse_decls(*decls)
        self.dest = self._parse_dest(dest, self.long_options, self.short_options)
        self.nvals = nvals
        self.required = required

    @staticmethod
    def _parse_decls(*decls: str) -> tuple[list[OptionElement], list[OptionElement]]:
        if not decls:
            raise CapfError("Invalid decls: At least one decl is required.")

        long_options: list[OptionElement] = []
        short_options: list[OptionElement] = []
        for decl in decls:
            if decl.startswith("--"):
                prefix, text = "--", decl[2:]
                if not text:
                    raise CapfError("Invalid decls: Empty string following prefix is not allowed.")
                if len(text) < 2:
                    raise CapfError(f"Invalid decls: Long option {decl!r} is too short.")
                long_options.append(OptionElement(prefix=prefix, text=text))
            elif decl.startswith("-"):
                prefix, text = "-", decl[1:]
                if not text:
                    raise CapfError("Invalid decls: Empty string following prefix is not allowed.")
                if len(text) > 1:
                    raise CapfError(f"Invalid decls: Short option {decl!r} is too long.")
                short_options.append(OptionElement(prefix=prefix, text=text))
            elif not decl:
                raise CapfError("Invalid decls: Empty string is not allowed.")
            else:
                raise CapfError(f"Invalid decls: {decl!r} does not start with prefix.")
        return long_options, short_options

    @staticmethod
    def _parse_dest(dest: str, long_options: list[OptionElement], short_options: list[OptionElement]) -> str:
        if dest:
            real_dest = dest
        elif long_options:
            real_dest = long_options[0].text
        else:
            real_dest = short_options[0].text
        real_dest = real_dest.replace("-", "_")
        _check_dest(real_dest)
        return real_dest


class Flag(Option):
    def __init__(self, *decls: str, dest: str = "") -> None:
        super().__init__(*decls, dest=dest, nvals=0, required=False)


class OptionGroup:
    def __init__(self, name: str) -> None:
        self.name = name
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

    def add_option(self, *args: Any, group: str = "", **kwargs: Any) -> Option:
        option = Option(*args, **kwargs)
        self.options.append(option)
        self._add_option_group(option, group)
        return option

    def add_flag(self, *args: Any, group: str = "", **kwargs: Any) -> Flag:
        flag = Flag(*args, **kwargs)
        self.options.append(flag)
        self._add_option_group(flag, group)
        return flag

    def _add_option_group(self, option: Option, group: str) -> None:
        group = group or "Options"
        option_group = self.option_groups.get(group)
        if option_group is None:
            option_group = OptionGroup(group)
            self.option_groups[group] = option_group
        option_group.add(option)


class Program:
    def __init__(self, name: str, version: str = "") -> None:
        self.name = name
        self.version = version

    def run(self, argv: Sequence[str] | None = None) -> None:
        argv = argv if argv is not None else sys.argv[1:]
