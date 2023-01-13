# Copyright 2013-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import os.path
import sys
from typing import TYPE_CHECKING

from xivo.cli import history
from xivo.cli.command.exit import ExitCommand
from xivo.cli.command.help import HelpCommand
from xivo.cli.command.unknown import PrintingUnknownCommand, _BaseUnknownCommand
from xivo.cli.completion.completer import CommandLineCompleter
from xivo.cli.completion.readline import ReadlineCompletionHelper
from xivo.cli.errorhandler import PrintTracebackErrorHandler, ReRaiseErrorHandler
from xivo.cli.executor import Executor
from xivo.cli.parser import RawCommandLineParser
from xivo.cli.registry import CommandRegistry
from xivo.cli.source.input import InputRawCommandLineSource

if TYPE_CHECKING:
    from .command.base import BaseCommand


class FacadeInterpreter:
    def __init__(
        self,
        prompt: str | None = None,
        history_file: str | None = None,
        error_handler: PrintTracebackErrorHandler | ReRaiseErrorHandler | None = None,
    ) -> None:
        if prompt is None:
            prompt = f'{os.path.basename(sys.argv[0])}> '
        if history_file:
            history_file = os.path.expanduser(history_file)
        self._prompt = prompt
        self._history_file = history_file
        self._command_registry = CommandRegistry()
        self._command_line_completer = CommandLineCompleter(self._command_registry)
        self._raw_command_line_parser = RawCommandLineParser(self._command_registry)
        self._error_handler = error_handler or PrintTracebackErrorHandler()
        self._unknown_command_class: type[_BaseUnknownCommand] = PrintingUnknownCommand

        self._add_std_commands()
        self._setup_completion()

    def _add_std_commands(self) -> None:
        self._command_registry.register_command('exit', ExitCommand())
        self._command_registry.register_command(
            'help', HelpCommand(self._command_registry)
        )

    def _setup_completion(self) -> None:
        completion_helper = ReadlineCompletionHelper(
            self._raw_command_line_parser, self._command_line_completer
        )
        completion_helper.setup()

    def add_command(self, name: str, command: BaseCommand) -> None:
        self._command_registry.register_command(name, command)

    def set_unknown_command_class(
        self, command_class: type[_BaseUnknownCommand]
    ) -> None:
        self._unknown_command_class = command_class

    def execute_command_line(self, raw_command_line: str) -> None:
        raw_command_line_source = [raw_command_line]
        executor = Executor(
            raw_command_line_source,
            self._raw_command_line_parser,
            self._error_handler,
            self._unknown_command_class,
        )
        executor.execute()

    def loop(
        self,
        error_handler: PrintTracebackErrorHandler | ReRaiseErrorHandler | None = None,
    ) -> None:
        error_handler = error_handler or self._error_handler
        raw_command_line_source = InputRawCommandLineSource(self._prompt)
        executor = Executor(
            raw_command_line_source,
            self._raw_command_line_parser,
            error_handler,
            self._unknown_command_class,
        )
        self._load_history()
        try:
            executor.execute()
        finally:
            self._save_history()

    def _load_history(self) -> None:
        if self._history_file:
            history.load(self._history_file)

    def _save_history(self) -> None:
        if self._history_file:
            history.save(self._history_file)
