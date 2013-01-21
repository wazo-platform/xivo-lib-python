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
from hamcrest import assert_that, equal_to, none
from mock import Mock
from xivo.cli.exception import NoMatchingCommandError
from xivo.cli.parser import RawCommandLineParser
from xivo.cli.registry import CommandRegistry


class TestRawCommandLineParser(unittest.TestCase):

    def setUp(self):
        self.command = Mock()
        self.command_registry = Mock(CommandRegistry)
        self.parser = RawCommandLineParser(self.command_registry)

    def test_parse_empty_line(self):
        raw_command_line = ''
        self.command_registry.get_command_and_args_from_words.side_effect = NoMatchingCommandError()

        command_line = self.parser.parse(raw_command_line)

        self.command_registry.get_command_and_args_from_words.assert_called_once_with([])
        assert_that(command_line.words, equal_to([]))
        assert_that(command_line.command, none())
        assert_that(command_line.command_args, none())

    def test_parse_one_letter_line(self):
        raw_command_line = 'h'
        self.command_registry.get_command_and_args_from_words.side_effect = NoMatchingCommandError()

        command_line = self.parser.parse(raw_command_line)

        self.command_registry.get_command_and_args_from_words.assert_called_once_with(['h'])
        assert_that(command_line.words, equal_to(['h']))
        assert_that(command_line.command, none())
        assert_that(command_line.command_args, none())

    def test_parse_one_letter_line_with_whitespaces(self):
        raw_command_line = ' h  \n'
        self.command_registry.get_command_and_args_from_words.side_effect = NoMatchingCommandError()

        command_line = self.parser.parse(raw_command_line)

        self.command_registry.get_command_and_args_from_words.assert_called_once_with(['h'])
        assert_that(command_line.words, equal_to(['h']))
        assert_that(command_line.command, none())
        assert_that(command_line.command_args, none())

    def test_parse_one_word_valid_line(self):
        raw_command_line = 'help'
        self.command_registry.get_command_and_args_from_words.return_value = (self.command, [])

        command_line = self.parser.parse(raw_command_line)

        self.command_registry.get_command_and_args_from_words.assert_called_once_with(['help'])
        assert_that(command_line.words, equal_to(['help']))
        assert_that(command_line.command, equal_to(self.command))
        assert_that(command_line.command_args, equal_to([]))

    def test_parse_one_word_valid_line_with_whitespaces(self):
        raw_command_line = ' help \n'
        self.command_registry.get_command_and_args_from_words.return_value = (self.command, [])

        command_line = self.parser.parse(raw_command_line)

        self.command_registry.get_command_and_args_from_words.assert_called_once_with(['help'])
        assert_that(command_line.words, equal_to(['help']))
        assert_that(command_line.command, equal_to(self.command))
        assert_that(command_line.command_args, equal_to([]))

    def test_parse_two_word_valid_line(self):
        raw_command_line = 'help foobar'
        self.command_registry.get_command_and_args_from_words.return_value = (self.command, ['foobar'])

        command_line = self.parser.parse(raw_command_line)

        self.command_registry.get_command_and_args_from_words.assert_called_once_with(['help', 'foobar'])
        assert_that(command_line.words, equal_to(['help', 'foobar']))
        assert_that(command_line.command, equal_to(self.command))
        assert_that(command_line.command_args, equal_to(['foobar']))
