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

from xivo.cli.exception import CommandAlreadyRegisteredError,\
    NoMatchingCommandError


class CommandRegistry(object):

    def __init__(self):
        self._commands = []

    def get_command_and_args_from_words(self, words):
        words_tuple = tuple(words)
        for command in self._commands:
            nb_words = command.nb_words
            if command.words == words_tuple[:nb_words]:
                return command._command, words[nb_words:]
        raise NoMatchingCommandError(words)

    def get_commands(self):
        return list(self._commands)

    def get_next_word(self, words):
        candidates = set()
        words_tuple = tuple(words)
        nb_words = len(words_tuple)
        for command in self._commands:
            if command.nb_words > nb_words and command.words[:nb_words] == words_tuple:
                candidates.add(command.words[nb_words])
        return list(candidates)

    def register_command(self, name, command):
        command_words = tuple(name.split(' '))
        if self._get_command(command_words) is not None:
            raise CommandAlreadyRegisteredError(name)
        self._commands.append(_NamedCommandDecorator(command, name, command_words))

    def _get_command(self, words_tuple):
        for command in self._commands:
            if command.words == words_tuple:
                return command
        return None


class _NamedCommandDecorator(object):

    def __init__(self, command, name, words):
        self._command = command
        self.name = name
        self.words = tuple(words)
        self.nb_words = len(words)

    def __getattr__(self, name):
        return getattr(self._command, name)
