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

from __future__ import print_function
from __future__ import unicode_literals

from xivo.cli.exception import UsageError


class Executor(object):

    def __init__(self, raw_command_line_source, raw_command_line_parser, error_handler, unknown_command_class):
        self._raw_command_line_source = raw_command_line_source
        self._raw_command_line_parser = raw_command_line_parser
        self._error_handler = error_handler
        self._unknown_command_class = unknown_command_class

    def execute(self):
        for raw_command_line in self._raw_command_line_source:
            self._process_next_command(raw_command_line)

    def _process_next_command(self, raw_command_line):
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
            print(command.format_usage())
        except Exception as e:
            self._error_handler.on_exception(e)
