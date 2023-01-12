# Copyright 2013-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from xivo.cli.exception import CommandAlreadyRegisteredError, NoMatchingCommandError

if TYPE_CHECKING:
    from .command.base import BaseCommand


class CommandRegistry:
    def __init__(self):
        self._commands: list[_NamedCommandDecorator] = []

    def complete_next_word(self, words: list[str]) -> list[str]:
        candidates = set()
        words_tuple = tuple(words)
        nb_words = len(words_tuple)
        for command in self._commands:
            if command.nb_words > nb_words and command.words[:nb_words] == words_tuple:
                candidates.add(command.words[nb_words])
        return list(candidates)

    def get_command(self, words: list[str]):
        words_tuple = tuple(words)
        command = self._get_command(words_tuple)
        if command is None:
            raise NoMatchingCommandError(words)
        return command

    def get_command_and_args(self, words: list[str]):
        words_tuple = tuple(words)
        for command in self._commands:
            nb_words = command.nb_words
            if command.words == words_tuple[:nb_words]:
                return command, words[nb_words:]
        raise NoMatchingCommandError(words)

    def get_commands(self) -> list[_NamedCommandDecorator]:
        return list(self._commands)

    def register_command(self, name: str, command: BaseCommand) -> None:
        command_words = tuple(name.split(' '))
        if self._get_command(command_words) is not None:
            raise CommandAlreadyRegisteredError(name)
        self._commands.append(_NamedCommandDecorator(command, name, command_words))

    def _get_command(
        self, words_tuple: tuple[str, ...]
    ) -> _NamedCommandDecorator | None:
        for command in self._commands:
            if command.words == words_tuple:
                return command
        return None


class _NamedCommandDecorator:
    def __init__(self, command: BaseCommand, name: str, words: Sequence[str]) -> None:
        self._command = command
        self.name = name
        self.words = tuple(words)
        self.nb_words = len(words)

    def format_usage(self) -> str:
        usage = self._command.usage
        if usage:
            return f'usage: {self.name} {usage}'
        return f'usage: {self.name}'

    def __getattr__(self, name: str) -> str:
        return getattr(self._command, name)
