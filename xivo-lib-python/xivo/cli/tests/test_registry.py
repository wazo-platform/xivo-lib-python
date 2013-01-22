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
from hamcrest import assert_that, equal_to
from mock import Mock
from xivo.cli.exception import CommandAlreadyRegisteredError, NoMatchingCommandError
from xivo.cli.registry import CommandRegistry


class TestCommandRegistry(unittest.TestCase):

    def setUp(self):
        self.command = Mock()
        self.command_registry = CommandRegistry()

    def test_get_command_and_args_when_exact_match(self):
        self.command_registry.register_command('foo bar', self.command)
        words = ['foo', 'bar']

        command, args = self.command_registry.get_command_and_args_from_words(words)

        assert_that(command, equal_to(self.command))
        assert_that(args, equal_to([]))

    def test_get_command_and_args_when_subset_match(self):
        self.command_registry.register_command('foo bar', self.command)
        words = ['foo', 'bar', '42']

        command, args = self.command_registry.get_command_and_args_from_words(words)

        assert_that(command, equal_to(self.command))
        assert_that(args, equal_to(['42']))

    def test_get_command_and_args_when_no_match(self):
        words = ['foo', 'bar', '42']

        self.assertRaises(NoMatchingCommandError,
                          self.command_registry.get_command_and_args_from_words, words)

    def test_get_commands(self):
        self.command_registry.register_command('foo bar', self.command)

        commands = self.command_registry.get_commands()

        assert_that(commands[0].name, equal_to('foo bar'))

    def test_get_next_word_when_no_words(self):
        command1 = self._new_command()
        command2 = self._new_command()
        command3 = self._new_command()
        self.command_registry.register_command('agents delete', command1)
        self.command_registry.register_command('users add', command2)
        self.command_registry.register_command('users list', command3)

        words = self.command_registry.get_next_word([])

        assert_that(words, equal_to(['agents', 'users']))

    def test_get_next_word_when_unknown_word(self):
        command1 = self._new_command()
        command2 = self._new_command()
        command3 = self._new_command()
        self.command_registry.register_command('agents delete', command1)
        self.command_registry.register_command('users add', command2)
        self.command_registry.register_command('users list', command3)

        words = self.command_registry.get_next_word(['xyz'])

        assert_that(words, equal_to([]))

    def test_get_next_word_when_known_word(self):
        command1 = self._new_command()
        command2 = self._new_command()
        command3 = self._new_command()
        self.command_registry.register_command('agents delete', command1)
        self.command_registry.register_command('users add', command2)
        self.command_registry.register_command('users list', command3)

        words = self.command_registry.get_next_word(['users'])

        assert_that(words, equal_to(['add', 'list']))

    def test_register_command_raise_error_if_already_registered(self):
        self.command_registry.register_command('foo bar', self.command)

        self.assertRaises(CommandAlreadyRegisteredError,
                          self.command_registry.register_command, 'foo bar', self.command)

    def _new_command(self):
        command = Mock()
        return command
