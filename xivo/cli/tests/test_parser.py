# Copyright 2013-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later


import unittest
from hamcrest import assert_that, equal_to, none
from unittest.mock import Mock
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
        self.command_registry.get_command_and_args.side_effect = (
            NoMatchingCommandError()
        )

        command_line = self.parser.parse(raw_command_line)

        self.command_registry.get_command_and_args.assert_called_once_with([])
        assert_that(command_line.words, equal_to([]))
        assert_that(command_line.command, none())
        assert_that(command_line.command_args, none())

    def test_parse_one_letter_line(self):
        raw_command_line = 'h'
        self.command_registry.get_command_and_args.side_effect = (
            NoMatchingCommandError()
        )

        command_line = self.parser.parse(raw_command_line)

        self.command_registry.get_command_and_args.assert_called_once_with(['h'])
        assert_that(command_line.words, equal_to(['h']))
        assert_that(command_line.command, none())
        assert_that(command_line.command_args, none())

    def test_parse_one_letter_line_with_whitespaces(self):
        raw_command_line = ' h  \n'
        self.command_registry.get_command_and_args.side_effect = (
            NoMatchingCommandError()
        )

        command_line = self.parser.parse(raw_command_line)

        self.command_registry.get_command_and_args.assert_called_once_with(['h'])
        assert_that(command_line.words, equal_to(['h']))
        assert_that(command_line.command, none())
        assert_that(command_line.command_args, none())

    def test_parse_one_word_valid_line(self):
        raw_command_line = 'help'
        self.command_registry.get_command_and_args.return_value = (self.command, [])

        command_line = self.parser.parse(raw_command_line)

        self.command_registry.get_command_and_args.assert_called_once_with(['help'])
        assert_that(command_line.words, equal_to(['help']))
        assert_that(command_line.command, equal_to(self.command))
        assert_that(command_line.command_args, equal_to([]))

    def test_parse_one_word_valid_line_with_whitespaces(self):
        raw_command_line = ' help \n'
        self.command_registry.get_command_and_args.return_value = (self.command, [])

        command_line = self.parser.parse(raw_command_line)

        self.command_registry.get_command_and_args.assert_called_once_with(['help'])
        assert_that(command_line.words, equal_to(['help']))
        assert_that(command_line.command, equal_to(self.command))
        assert_that(command_line.command_args, equal_to([]))

    def test_parse_two_word_valid_line(self):
        raw_command_line = 'help foobar'
        self.command_registry.get_command_and_args.return_value = (
            self.command,
            ['foobar'],
        )

        command_line = self.parser.parse(raw_command_line)

        self.command_registry.get_command_and_args.assert_called_once_with(
            ['help', 'foobar']
        )
        assert_that(command_line.words, equal_to(['help', 'foobar']))
        assert_that(command_line.command, equal_to(self.command))
        assert_that(command_line.command_args, equal_to(['foobar']))
