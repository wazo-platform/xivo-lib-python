# -*- coding: utf-8 -*-

# Copyright (C) 2013 Avencall
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
from xivo.cli.completion.completer import CommandLineCompleter
from xivo.cli.registry import CommandRegistry


class TestCompleter(unittest.TestCase):

    def setUp(self):
        self.command_registry = Mock(CommandRegistry)
        self.command_registry.complete_next_word.return_value = ['agents', 'users']
        self.completer = CommandLineCompleter(self.command_registry)

    def test_complete_next_word_empty_line(self):
        words = []

        candidates = self.completer.complete_next_word(words)

        self.command_registry.complete_next_word.assert_called_once_with([])
        assert_that(candidates, equal_to(['agents', 'users']))

    def test_complete_last_word_one_valid_letter(self):
        words = ['a']

        candidates = self.completer.complete_last_word(words)

        self.command_registry.complete_next_word.assert_called_once_with([])
        assert_that(candidates, equal_to(['agents']))

    def test_complete_last_word_one_invalid_letter(self):
        words = ['x']

        candidates = self.completer.complete_last_word(words)

        self.command_registry.complete_next_word.assert_called_once_with([])
        assert_that(candidates, equal_to([]))

    def test_complete_last_word_one_valid_word(self):
        words = ['agents']

        candidates = self.completer.complete_last_word(words)

        self.command_registry.complete_next_word.assert_called_once_with([])
        assert_that(candidates, equal_to(['agents']))

    def test_complete_next_word_one_valid_word(self):
        words = ['users']

        candidates = self.completer.complete_next_word(words)

        self.command_registry.complete_next_word.assert_called_once_with(['users'])
        assert_that(candidates, equal_to(['agents', 'users']))

    def test_complete_last_word_two_valid_words(self):
        words = ['users', 'a']

        candidates = self.completer.complete_last_word(words)

        self.command_registry.complete_next_word.assert_called_once_with(['users'])
        assert_that(candidates, equal_to(['agents']))
