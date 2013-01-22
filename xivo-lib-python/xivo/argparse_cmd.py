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
import sys


def execute_command(command, args=None):
    if args is None:
        args = sys.argv[1:]
    command_executor = CommandExecutor(command)
    command_executor.execute(args)


class CommandExecutor(object):
    def __init__(self, command):
        self._command = command

    def execute(self, args):
        parser = self._command.create_parser()
        self._command.configure_parser(parser)

        subcommands = self._command.create_subcommands()
        self._command.configure_subcommands(subcommands)
        subcommands.configure_parser(parser)

        parsed_args = parser.parse_args(args)

        self._command.pre_execute(parsed_args)
        try:
            subcommands.execute(parsed_args)
        finally:
            self._command.post_execute(parsed_args)


class AbstractCommand(object):
    def create_parser(self):
        return argparse.ArgumentParser()

    def configure_parser(self, parser):
        pass

    def create_subcommands(self):
        return Subcommands()

    def configure_subcommands(self, subcommands):
        raise Exception('must be overriden in derived class')

    def pre_execute(self, parsed_args):
        pass

    def post_execute(self, parsed_args):
        pass


class Subcommands(object):
    def __init__(self):
        self._subcommands = []

    def add_subcommand(self, subcommand):
        self._subcommands.append(subcommand)

    def configure_parser(self, parser):
        subparsers = parser.add_subparsers()
        for subcommand in self._subcommands:
            subcommand_parser = subparsers.add_parser(subcommand.name)
            subcommand_parser.set_defaults(_subcommand=subcommand)
            subcommand.configure_parser(subcommand_parser)

    def execute(self, parsed_args):
        subcommand = parsed_args._subcommand
        subcommand.execute(parsed_args)


class AbstractSubcommand(object):
    def __init__(self, name):
        self.name = name

    def configure_parser(self, parser):
        pass

    def execute(self, parsed_args):
        raise Exception('must be overriden in derived class')
