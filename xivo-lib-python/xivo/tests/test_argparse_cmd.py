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

import argparse
import mock
import sys
import unittest
from xivo.argparse_cmd import AbstractSubcommand, Subcommands, \
    CommandExecutor, AbstractCommand, execute_command


def _new_parser():
    return argparse.ArgumentParser()


def _first_call_args(mock):
    assert mock.called
    return mock.call_args[0][0]


class TestExecuteCommand(unittest.TestCase):
    def setUp(self):
        self.mock_parser = mock.Mock()
        self.mock_parser.parse_args.return_value = mock.sentinel.ReturnValue
        self.mock_command = mock.Mock(spec=AbstractCommand)
        self.mock_command.create_parser.return_value = self.mock_parser

    def test_command_is_called_with_args_when_args_given(self):
        args = ['foo']
        execute_command(self.mock_command, args)

        self.mock_parser.parse_args.assert_called_once_with(args)
        self.mock_command.pre_execute.assert_called_once_with(mock.sentinel.ReturnValue)

    def test_command_is_called_with_sys_argv_when_args_not_given(self):
        execute_command(self.mock_command)

        self.mock_parser.parse_args.assert_called_once_with(sys.argv[1:])
        self.mock_command.pre_execute.assert_called_once_with(mock.sentinel.ReturnValue)


class TestCommandExecutor(unittest.TestCase):
    def setUp(self):
        self.mock_parser = mock.Mock()
        self.mock_parser.parse_args.return_value = mock.sentinel.ReturnValue
        self.mock_subcommand = mock.Mock()
        self.mock_command = mock.Mock(spec=AbstractCommand)
        self.mock_command.create_parser.return_value = self.mock_parser
        self.mock_command.create_subcommands.return_value = self.mock_subcommand
        self.command_executor = CommandExecutor(self.mock_command)

    def test_execute_calls_command_create_parser(self):
        self.command_executor.execute([])

        self.mock_command.create_parser.assert_called_once_with()

    def test_execute_calls_command_configure_parser(self):
        self.command_executor.execute([])

        self.mock_command.configure_parser.assert_called_once_with(self.mock_parser)

    def test_execute_calls_command_create_subcommands(self):
        self.command_executor.execute([])

        self.mock_command.create_subcommands.assert_called_once_with()

    def test_execute_calls_command_configure_subcommands(self):
        self.command_executor.execute([])

        self.mock_command.configure_subcommands.assert_called_once_with(self.mock_subcommand)

    def test_execute_calls_subcommand_configure_parser(self):
        self.command_executor.execute([])

        self.mock_subcommand.configure_parser.assert_called_once_with(self.mock_parser)

    def test_execute_calls_command_pre_execute_with_parsed_args(self):
        self.command_executor.execute([])

        self.mock_command.pre_execute.assert_called_once_with(mock.sentinel.ReturnValue)

    def test_execute_calls_subcommand_execute(self):
        self.command_executor.execute([])

        self.mock_subcommand.execute.assert_called_once_with(mock.sentinel.ReturnValue)


class TestAbstractCommand(unittest.TestCase):
    def setUp(self):
        self.command = AbstractCommand()

    def test_create_parser_returns_argument_parser(self):
        parser = self.command.create_parser()

        self.assertTrue(isinstance(parser, argparse.ArgumentParser))

    def test_configure_parser_does_nothing(self):
        mock_parser = mock.Mock()

        self.command.configure_parser(mock_parser)

        self.assertEqual([], mock_parser.method_calls)

    def test_create_subcommands_returns_subcommands(self):
        subcommands = self.command.create_subcommands()

        self.assertTrue(isinstance(subcommands, Subcommands))

    def test_configure_subcommands_raises_exception(self):
        mock_subcommands = mock.Mock(spec=Subcommands)

        self.assertRaises(Exception, self.command.configure_subcommands, mock_subcommands)

    def test_pre_execute_does_nothing(self):
        mock_parsed_args = mock.Mock()

        self.command.pre_execute(mock_parsed_args)

        self.assertEqual([], mock_parsed_args.method_calls)


class TestSubcommands(unittest.TestCase):
    def setUp(self):
        self.subcommands = Subcommands()

    def test_add_subcommand_appends_element_to_list(self):
        self.subcommands.add_subcommand(mock.sentinel.Arg)

        self.assertEqual([mock.sentinel.Arg], self.subcommands._subcommands)

    def test_configure_parser_calls_subcommands_configure_parser(self):
        foo_subcommand = self._new_mock_subcommand('foo')

        self.subcommands.add_subcommand(foo_subcommand)
        self.subcommands.configure_parser(_new_parser())

        self.assertTrue(foo_subcommand.configure_parser.called)
        self.assertTrue(isinstance(_first_call_args(foo_subcommand.configure_parser),
                                   argparse.ArgumentParser))

    def _new_mock_subcommand(self, name):
        mock_subcommand = mock.Mock(spec=AbstractSubcommand)
        mock_subcommand.name = name
        return mock_subcommand

    def test_execute_calls_subcommand_execute_with_one_subcommand(self):
        foo_subcommand = self._new_mock_subcommand('foo')
        parser = _new_parser()

        self.subcommands.add_subcommand(foo_subcommand)
        self.subcommands.configure_parser(parser)
        parsed_args = parser.parse_args(['foo'])
        self.subcommands.execute(parsed_args)

        foo_subcommand.execute.assert_called_once_with(parsed_args)

    def test_execute_calls_subcommand_execute_with_two_subcommands(self):
        foo_subcommand = self._new_mock_subcommand('foo')
        bar_subcommand = self._new_mock_subcommand('bar')
        parser = _new_parser()

        self.subcommands.add_subcommand(foo_subcommand)
        self.subcommands.add_subcommand(bar_subcommand)
        self.subcommands.configure_parser(parser)
        parsed_args = parser.parse_args(['bar'])
        self.subcommands.execute(parsed_args)

        bar_subcommand.execute.assert_called_once_with(parsed_args)
        self.assertFalse(foo_subcommand.execute.called)


class TestAbstractSubcommand(unittest.TestCase):
    SUBCOMMAND_NAME = 'foo'

    def setUp(self):
        self.subcommand = AbstractSubcommand(self.SUBCOMMAND_NAME)

    def test_name_attribute_is_the_same_as_constructor(self):
        self.assertEqual(self.SUBCOMMAND_NAME, self.subcommand.name)

    def test_configure_parser_does_nothing(self):
        mock_parser = mock.Mock()

        self.subcommand.configure_parser(mock_parser)

        self.assertEqual([], mock_parser.method_calls)

    def test_execute_raises_exception(self):
        mock_parsed_args = mock.Mock()

        self.assertRaises(Exception, self.subcommand.execute, mock_parsed_args)
