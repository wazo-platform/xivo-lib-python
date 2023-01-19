# Copyright 2013-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later


import unittest
from unittest.mock import Mock

from hamcrest import assert_that, contains_inanyorder, equal_to

from xivo.cli.exception import CommandAlreadyRegisteredError, NoMatchingCommandError
from xivo.cli.registry import CommandRegistry


class TestCommandRegistry(unittest.TestCase):
    def setUp(self):
        self.command = Mock()
        self.command_registry = CommandRegistry()

    def test_get_command_and_args_when_exact_match(self):
        self.command_registry.register_command('foo bar', self.command)
        words = ['foo', 'bar']

        command, args = self.command_registry.get_command_and_args(words)

        assert_that(command._command, equal_to(self.command))
        assert_that(args, equal_to([]))

    def test_get_command_and_args_when_subset_match(self):
        self.command_registry.register_command('foo bar', self.command)
        words = ['foo', 'bar', '42']

        command, args = self.command_registry.get_command_and_args(words)

        assert_that(command._command, equal_to(self.command))
        assert_that(args, equal_to(['42']))

    def test_get_command_and_args_when_no_match(self):
        words = ['foo', 'bar', '42']

        self.assertRaises(
            NoMatchingCommandError, self.command_registry.get_command_and_args, words
        )

    def test_get_commands(self):
        self.command_registry.register_command('foo bar', self.command)

        commands = self.command_registry.get_commands()

        assert_that(commands[0].name, equal_to('foo bar'))

    def test_complete_next_word_when_no_words(self):
        command1 = self._new_command()
        command2 = self._new_command()
        command3 = self._new_command()
        self.command_registry.register_command('agents delete', command1)
        self.command_registry.register_command('users add', command2)
        self.command_registry.register_command('users list', command3)

        words = self.command_registry.complete_next_word([])

        assert_that(words, contains_inanyorder('agents', 'users'))

    def test_complete_next_word_when_unknown_word(self):
        command1 = self._new_command()
        command2 = self._new_command()
        command3 = self._new_command()
        self.command_registry.register_command('agents delete', command1)
        self.command_registry.register_command('users add', command2)
        self.command_registry.register_command('users list', command3)

        words = self.command_registry.complete_next_word(['xyz'])

        assert_that(words, equal_to([]))

    def test_complete_next_word_when_known_word(self):
        command1 = self._new_command()
        command2 = self._new_command()
        command3 = self._new_command()
        self.command_registry.register_command('agents delete', command1)
        self.command_registry.register_command('users add', command2)
        self.command_registry.register_command('users list', command3)

        words = self.command_registry.complete_next_word(['users'])

        assert_that(words, contains_inanyorder('add', 'list'))

    def test_register_command_raise_error_if_already_registered(self):
        self.command_registry.register_command('foo bar', self.command)

        self.assertRaises(
            CommandAlreadyRegisteredError,
            self.command_registry.register_command,
            'foo bar',
            self.command,
        )

    def _new_command(self):
        command = Mock()
        return command
