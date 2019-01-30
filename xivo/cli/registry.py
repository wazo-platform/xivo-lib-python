# -*- coding: utf-8 -*-
# Copyright (C) 2013-2014 Avencall
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import unicode_literals

from xivo.cli.exception import CommandAlreadyRegisteredError,\
    NoMatchingCommandError


class CommandRegistry(object):

    def __init__(self):
        self._commands = []

    def complete_next_word(self, words):
        candidates = set()
        words_tuple = tuple(words)
        nb_words = len(words_tuple)
        for command in self._commands:
            if command.nb_words > nb_words and command.words[:nb_words] == words_tuple:
                candidates.add(command.words[nb_words])
        return list(candidates)

    def get_command(self, words):
        words_tuple = tuple(words)
        command = self._get_command(words_tuple)
        if command is None:
            raise NoMatchingCommandError(words)
        return command

    def get_command_and_args(self, words):
        words_tuple = tuple(words)
        for command in self._commands:
            nb_words = command.nb_words
            if command.words == words_tuple[:nb_words]:
                return command, words[nb_words:]
        raise NoMatchingCommandError(words)

    def get_commands(self):
        return list(self._commands)

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

    def format_usage(self):
        usage = self._command.usage
        if usage:
            return 'usage: {0} {1}'.format(self.name, usage)
        else:
            return 'usage: {0}'.format(self.name)

    def __getattr__(self, name):
        return getattr(self._command, name)
