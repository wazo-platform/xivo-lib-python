# -*- coding: UTF-8 -*-

# Copyright (C) 2013  Avencall
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


class HelpCommand(BaseCommand):

    help = 'Display help about commands'

    def __init__(self, command_registry):
        BaseCommand.__init__(self)
        self._command_registry = command_registry

    def execute(self):
        commands = self._command_registry.get_commands()
        commands.sort(key=attrgetter('name'))
        max_name_length = max(len(command.name) for command in commands)
        for command in commands:
            print(command.name.ljust(max_name_length), getattr(command, 'help', '---'))
