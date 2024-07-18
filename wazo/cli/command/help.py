# Copyright 2013-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from operator import attrgetter
from typing import TYPE_CHECKING

from xivo.cli.command.base import BaseCommand
from xivo.cli.exception import NoMatchingCommandError

if TYPE_CHECKING:
    from ..registry import CommandRegistry


class HelpCommand(BaseCommand):
    help = 'Display help about commands'
    usage = '[<command_name>]'

    def __init__(self, command_registry: CommandRegistry) -> None:
        super().__init__()
        self._command_registry = command_registry

    def prepare(self, command_args: list[str] | None) -> tuple[list[str] | None, ...]:
        if command_args:
            words = command_args
        else:
            words = None
        return (words,)

    def execute(self, words: list[str]) -> None:
        if words is None:
            self._show_all()
        else:
            self._show(words)

    def _show_all(self) -> None:
        commands = self._command_registry.get_commands()
        commands.sort(key=attrgetter('name'))
        max_name_length = max(len(command.name) for command in commands)
        for command in commands:
            print(command.name.ljust(max_name_length), command.help)

    def _show(self, words: list[str]) -> None:
        try:
            command = self._command_registry.get_command(words)
        except NoMatchingCommandError:
            print(f'error: no such command "{" ".join(words)}"')
        else:
            print(command.format_usage())
