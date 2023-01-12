# Copyright 2013-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from xivo.cli.exception import UsageError

if TYPE_CHECKING:
    from .errorhandler import PrintTracebackErrorHandler, ReRaiseErrorHandler
    from .parser import RawCommandLineParser
    from .command.unknown import _BaseUnknownCommand


class Executor:
    def __init__(
        self,
        raw_command_line_source: Iterable[str],
        raw_command_line_parser: RawCommandLineParser,
        error_handler: PrintTracebackErrorHandler | ReRaiseErrorHandler,
        unknown_command_class: type[_BaseUnknownCommand],
    ) -> None:
        self._raw_command_line_source = raw_command_line_source
        self._raw_command_line_parser = raw_command_line_parser
        self._error_handler = error_handler
        self._unknown_command_class = unknown_command_class

    def execute(self) -> None:
        for raw_command_line in self._raw_command_line_source:
            self._process_next_command(raw_command_line)

    def _process_next_command(self, raw_command_line: str) -> None:
        command_line = self._raw_command_line_parser.parse(raw_command_line)
        if command_line.is_blank():
            return

        if command_line.command is None:
            command = self._unknown_command_class(command_line.words)
        else:
            command = command_line.command

        try:
            execute_args = command.prepare(command_line.command_args)
            command.execute(*execute_args)
        except UsageError:
            print(command.format_usage())  # type: ignore[attr-defined]
        except Exception as e:
            self._error_handler.on_exception(e)
