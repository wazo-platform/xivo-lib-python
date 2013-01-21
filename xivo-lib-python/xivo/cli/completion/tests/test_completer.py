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

import unittest
from mock import Mock
from hamcrest import assert_that, equal_to
from xivo.cli.commandline import CommandLine
from xivo.cli.completion.completer import CommandLineCompleter
from xivo.cli.registry import CommandRegistry


class TestCompleter(unittest.TestCase):

    def setUp(self):
        self.command_registry = Mock(CommandRegistry)
        self.command_registry.get_next_word.return_value = ['agents', 'users']
        self.completer = CommandLineCompleter(self.command_registry)

    def test_complete_next_word_empty_line(self):
        command_line = self._new_command_line('')

        candidates = self.completer.complete_next_word(command_line)

        self.command_registry.get_next_word.assert_called_once_with([])
        assert_that(candidates, equal_to(['agents', 'users']))

    def test_complete_last_word_one_valid_letter(self):
        command_line = self._new_command_line('a')

        candidates = self.completer.complete_last_word(command_line)

        self.command_registry.get_next_word.assert_called_once_with([])
        assert_that(candidates, equal_to(['agents']))

    def test_complete_last_word_one_invalid_letter(self):
        command_line = self._new_command_line('x')

        candidates = self.completer.complete_last_word(command_line)

        self.command_registry.get_next_word.assert_called_once_with([])
        assert_that(candidates, equal_to([]))

    def test_complete_last_word_one_valid_word(self):
        command_line = self._new_command_line('agents')

        candidates = self.completer.complete_last_word(command_line)

        self.command_registry.get_next_word.assert_called_once_with([])
        assert_that(candidates, equal_to(['agents']))

    def test_complete_next_word_one_valid_word(self):
        command_line = self._new_command_line('users')

        candidates = self.completer.complete_next_word(command_line)

        self.command_registry.get_next_word.assert_called_once_with(['users'])
        assert_that(candidates, equal_to(['agents', 'users']))

    def test_complete_last_word_two_valid_words(self):
        command_line = self._new_command_line('users a')

        candidates = self.completer.complete_last_word(command_line)

        self.command_registry.get_next_word.assert_called_once_with(['users'])
        assert_that(candidates, equal_to(['agents']))

    def _new_command_line(self, raw_command_line):
        return CommandLine(raw_command_line.split(), None, None)
