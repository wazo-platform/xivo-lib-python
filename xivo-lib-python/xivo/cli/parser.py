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

from __future__ import unicode_literals

from xivo.cli.commandline import CommandLine
from xivo.cli.exception import NoMatchingCommandError


class RawCommandLineParser(object):

    word_delimiter = ' '

    def __init__(self, command_registry):
        self.command_registry = command_registry

    def parse(self, raw_command_line):
        words = raw_command_line.split()
        try:
            command, command_args = self.command_registry.get_command_and_args_from_words(words)
        except NoMatchingCommandError:
            command = None
            command_args = None
        return CommandLine(words, command, command_args)
