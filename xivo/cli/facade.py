# -*- coding: utf-8 -*-

# Copyright 2013-2017 The Wazo Authors  (see the AUTHORS file)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from __future__ import unicode_literals

import os.path
import sys
from xivo.cli import history
from xivo.cli.command.help import HelpCommand
from xivo.cli.command.exit import ExitCommand
from xivo.cli.command.unknown import PrintingUnknownCommand
from xivo.cli.completion.completer import CommandLineCompleter
from xivo.cli.completion.readline import ReadlineCompletionHelper
from xivo.cli.errorhandler import PrintTracebackErrorHandler
from xivo.cli.executor import Executor
from xivo.cli.parser import RawCommandLineParser
from xivo.cli.registry import CommandRegistry
from xivo.cli.source.input import InputRawCommandLineSource


class FacadeInterpreter(object):

    def __init__(self, prompt=None, history_file=None, error_handler=None):
        if prompt is None:
            prompt = '{0}> '.format(os.path.basename(sys.argv[0]))
        if history_file:
            history_file = os.path.expanduser(history_file)
        self._prompt = prompt
        self._history_file = history_file
        self._command_registry = CommandRegistry()
        self._command_line_completer = CommandLineCompleter(self._command_registry)
        self._raw_command_line_parser = RawCommandLineParser(self._command_registry)
        self._error_handler = error_handler or PrintTracebackErrorHandler()
        self._unknown_command_class = PrintingUnknownCommand

        self._add_std_commands()
        self._setup_completion()

    def _add_std_commands(self):
        self._command_registry.register_command('exit', ExitCommand())
        self._command_registry.register_command('help', HelpCommand(self._command_registry))

    def _setup_completion(self):
        completion_helper = ReadlineCompletionHelper(self._raw_command_line_parser,
                                                     self._command_line_completer)
        completion_helper.setup()

    def add_command(self, name, command):
        self._command_registry.register_command(name, command)

    def set_unknown_command_class(self, command_class):
        self._unknown_command_class = command_class

    def execute_command_line(self, raw_command_line):
        raw_command_line_source = [raw_command_line]
        executor = Executor(raw_command_line_source,
                            self._raw_command_line_parser,
                            self._error_handler,
                            self._unknown_command_class)
        executor.execute()

    def loop(self, error_handler=None):
        error_handler = error_handler or self._error_handler
        raw_command_line_source = InputRawCommandLineSource(self._prompt)
        executor = Executor(raw_command_line_source,
                            self._raw_command_line_parser,
                            error_handler,
                            self._unknown_command_class)
        self._load_history()
        try:
            executor.execute()
        finally:
            self._save_history()

    def _load_history(self):
        if self._history_file:
            history.load(self._history_file)

    def _save_history(self):
        if self._history_file:
            history.save(self._history_file)
