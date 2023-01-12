# Copyright 2013-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .command.base import BaseCommand


class CommandLine:
    def __init__(
        self, words: list[str], command: BaseCommand, command_args: list[str]
    ) -> None:
        self.words = words
        self.command = command
        self.command_args = command_args

    def is_blank(self) -> bool:
        return not self.words
