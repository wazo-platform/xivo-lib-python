# -*- coding: utf-8 -*-

# Copyright (C) 2013-2014 Avencall
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

from operator import attrgetter
from xivo.cli.command.base import BaseCommand
from xivo.cli.exception import NoMatchingCommandError


class HelpCommand(BaseCommand):

    help = 'Display help about commands'
    usage = '[<command_name>]'

    def __init__(self, command_registry):
        BaseCommand.__init__(self)
        self._command_registry = command_registry

    def prepare(self, command_args):
        if command_args:
            words = command_args
        else:
            words = None
        return (words,)

    def execute(self, words):
        if words is None:
            self._show_all()
        else:
            self._show(words)

    def _show_all(self):
        commands = self._command_registry.get_commands()
        commands.sort(key=attrgetter('name'))
        max_name_length = max(len(command.name) for command in commands)
        for command in commands:
            print(command.name.ljust(max_name_length), command.help)

    def _show(self, words):
        try:
            command = self._command_registry.get_command(words)
        except NoMatchingCommandError:
            print('error: no such command "{0}"'.format(' '.join(words)))
        else:
            print(command.format_usage())
