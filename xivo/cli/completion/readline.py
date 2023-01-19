# Copyright 2013-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import readline
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..parser import RawCommandLineParser
    from .completer import CommandLineCompleter


class ReadlineCompletionHelper:
    def __init__(
        self,
        raw_command_line_parser: RawCommandLineParser,
        command_line_completer: CommandLineCompleter,
    ) -> None:
        self._raw_command_line_parser = raw_command_line_parser
        self._command_line_completer = command_line_completer
        self._candidates: list[str] = []

    def setup(self) -> None:
        readline.parse_and_bind('tab: complete')
        readline.set_completer_delims(self._raw_command_line_parser.word_delimiter)
        readline.set_completer(self.on_readline_complete)

    def on_readline_complete(self, text: str, state: int) -> str | None:
        if state == 0:
            self._refresh_candidates(text)

        try:
            response = self._candidates[state]
        except IndexError:
            response = None
        return response

    def _refresh_candidates(self, text: str) -> None:
        raw_command_line = self._get_raw_command_line()
        words = self._raw_command_line_parser.split(raw_command_line)
        if text:
            self._candidates = self._command_line_completer.complete_last_word(words)
        else:
            self._candidates = self._command_line_completer.complete_next_word(words)

        if len(self._candidates) == 1:
            self._candidates[0] += self._raw_command_line_parser.word_delimiter

    def _get_raw_command_line(self) -> str:
        line_buffer = readline.get_line_buffer()
        end_idx = readline.get_endidx()
        raw_command_line = line_buffer[:end_idx]
        return raw_command_line
