# Copyright 2013-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..registry import CommandRegistry


class CommandLineCompleter:
    def __init__(self, command_registry: CommandRegistry) -> None:
        self._command_registry = command_registry

    def complete_last_word(self, words: list[str]) -> list[str]:
        last_word = words[-1]
        candidates = self._command_registry.complete_next_word(words[:-1])
        return sorted(
            candidate for candidate in candidates if candidate.startswith(last_word)
        )

    def complete_next_word(self, words: list[str]) -> list[str]:
        candidates = self._command_registry.complete_next_word(words)
        return sorted(candidates)
