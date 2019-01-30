# -*- coding: utf-8 -*-
# Copyright (C) 2013-2014 Avencall
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import unicode_literals

from xivo.cli.commandline import CommandLine
from xivo.cli.exception import NoMatchingCommandError


class RawCommandLineParser(object):

    word_delimiter = ' '

    def __init__(self, command_registry):
        self.command_registry = command_registry

    def split(self, raw_command_line):
        return raw_command_line.split()

    def parse(self, raw_command_line):
        words = self.split(raw_command_line)
        try:
            command, command_args = self.command_registry.get_command_and_args(words)
        except NoMatchingCommandError:
            command = None
            command_args = None
        return CommandLine(words, command, command_args)
