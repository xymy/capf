from dataclasses import dataclass

from .adaptors import Adaptor, ValueSource
from .core import Argument, Command, Option
from .exceptions import CliParsingError
from .reader import Reader


class CommandConsumer:
    def __init__(self, command: Command) -> None:
        self.cmap = self._build(command)

    @staticmethod
    def _build(command: Command) -> dict[str, Command]:
        cmap: dict[str, Command] = {}
        for command_group in command.command_groups:
            for subcommand in command_group:
                cmap[subcommand.name] = subcommand
        return cmap

    def consume(self, token: str) -> Command:
        subcommand = self.cmap.get(token, None)
        if subcommand is None:
            raise CliParsingError(f"Unknown command: {token!r}.")
        return subcommand


class ArgumentConsumer:
    def __init__(self, command: Command) -> None:
        self.aseq = self._build(command)
        self.areader = Reader(self.aseq)

    @staticmethod
    def _build(command: Command) -> list[Argument]:
        aseq: list[Argument] = []
        for argument_group in command.argument_groups:
            for argument in argument_group:
                aseq.append(argument)
        return aseq

    def consume(self, token: str) -> None:
        if self.areader.is_eof():
            raise CliParsingError(f"Too many arguments: {token!r}.")
        argument = self.areader.get()
        argument.adaptor([token], source=ValueSource.CLI)
        if argument.multiple:
            self.areader.put()


class OptionConsumer:
    def __init__(self, command: Command) -> None:
        self.smap, self.lmap = self._build(command)

    @staticmethod
    def _build(command: Command) -> tuple[dict[str, Option], dict[str, Option]]:
        smap: dict[str, Option] = {}
        lmap: dict[str, Option] = {}
        for option_group in command.option_groups:
            for option in option_group:
                for short_option in option.short_options:
                    if short_option in smap:
                        raise ValueError(
                            f"Short option {short_option!r} conflict detected."
                        )
                    smap[short_option] = option
                for long_option in option.long_options:
                    if long_option in lmap:
                        raise ValueError(
                            f"Long option {long_option!r} conflict detected."
                        )
                    lmap[long_option] = option
        return smap, lmap

    def consume_long(self, token: str, reader: Reader) -> None:
        token = token.removeprefix("--")
        if "=" in token:  # --option=value
            name, value = token.split("=", 1)
            _, adaptor = self._get_long_option(name)
            if adaptor.num_values == 0:
                raise CliParsingError(
                    f"Option --{name!r} does not take a value."
                )
            adaptor([value], source=ValueSource.CLI)
        else:  # --option [value]
            _, adaptor = self._get_long_option(token)
            if adaptor.num_values == 0:
                adaptor([], source=ValueSource.CLI)
            else:
                if reader.is_eof():
                    raise CliParsingError(
                        f"Option --{token!r} requires a value."
                    )
                adaptor([reader.get()], source=ValueSource.CLI)

    def consume_short(self, token: str, reader: Reader[str]) -> None:
        token = token.removeprefix("-")
        creader = Reader(token)
        while not creader.is_eof():
            name = creader.get()
            _, adaptor = self._get_short_option(name)
            if adaptor.num_values == 0:
                adaptor([], source=ValueSource.CLI)
            else:
                if not creader.is_eof():  # -ovalue
                    value = token[creader.cursor :]
                else:  # -o value
                    if reader.is_eof():
                        raise CliParsingError(
                            f"Option -{name!r} requires a value."
                        )
                    value = reader.get()
                adaptor([value], source=ValueSource.CLI)
                break  # end of parsing

    def _get_long_option(self, name: str) -> tuple[Option, Adaptor]:
        option = self.lmap.get(name, None)
        if option is None:
            raise CliParsingError(f"Unknown option: {name!r}.")
        return option, option.adaptor

    def _get_short_option(self, name: str) -> tuple[Option, Adaptor]:
        option = self.smap.get(name, None)
        if option is None:
            raise CliParsingError(f"Unknown option: {name!r}.")
        return option, option.adaptor


@dataclass
class ParserResult:
    command: Command | None = None


class Parser:
    def __init__(self, command: Command) -> None:
        if command.command_groups and command.argument_groups:
            raise ValueError(
                "Command can not have both command groups and argument groups."
            )
        self.command = command
        self.command_consumer = CommandConsumer(command)
        self.argument_consumer = ArgumentConsumer(command)
        self.option_consumer = OptionConsumer(command)

    def parse(self, reader: Reader[str]) -> ParserResult:
        if self.command.is_leaf():
            result = self._parse_leaf(reader)
        else:
            result = self._parse_node(reader)
        return result

    def _parse_leaf(self, reader: Reader[str]) -> ParserResult:
        double_hyphen = False
        while not reader.is_eof():
            token = reader.get()
            if token == "--":  # noqa: S105
                double_hyphen = True
                break

            if token.startswith("--"):
                self.option_consumer.consume_long(token, reader)
            elif token.startswith("-"):
                self.option_consumer.consume_short(token, reader)
            else:
                self.argument_consumer.consume(token)

        if double_hyphen:
            while not reader.is_eof():
                token = reader.get()
                self.argument_consumer.consume(token)
        return ParserResult()

    def _parse_node(self, reader: Reader[str]) -> ParserResult:
        double_hyphen = False
        while not reader.is_eof():
            token = reader.get()
            if token == "--":  # noqa: S105
                double_hyphen = True
                break

            if token.startswith("--"):
                self.option_consumer.consume_long(token, reader)
            elif token.startswith("-"):
                self.option_consumer.consume_short(token, reader)
            else:
                subcomand = self.command_consumer.consume(token)
                return ParserResult(subcomand)

        if double_hyphen:
            while not reader.is_eof():
                token = reader.get()
                subcomand = self.command_consumer.consume(token)
                return ParserResult(subcomand)
        return ParserResult()
