# -*- coding: utf-8 -*-
# Copyright (C) 2013-2014 Avencall
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import
from __future__ import unicode_literals

import readline


class ReadlineCompletionHelper(object):

    def __init__(self, raw_command_line_parser, command_line_completer):
        self._raw_command_line_parser = raw_command_line_parser
        self._command_line_completer = command_line_completer
        self._candidates = []

    def setup(self):
        readline.parse_and_bind('tab: complete')
        readline.set_completer_delims(self._raw_command_line_parser.word_delimiter)
        readline.set_completer(self.on_readline_complete)

    def on_readline_complete(self, text, state):
        if state == 0:
            self._refresh_candidates(text)

        try:
            response = self._candidates[state]
        except IndexError:
            response = None
        return response

    def _refresh_candidates(self, text):
        raw_command_line = self._get_raw_command_line()
        words = self._raw_command_line_parser.split(raw_command_line)
        if text:
            self._candidates = self._command_line_completer.complete_last_word(words)
        else:
            self._candidates = self._command_line_completer.complete_next_word(words)

        if len(self._candidates) == 1:
            self._candidates[0] += self._raw_command_line_parser.word_delimiter

    def _get_raw_command_line(self):
        line_buffer = readline.get_line_buffer()
        end_idx = readline.get_endidx()
        raw_command_line = line_buffer[:end_idx]
        return raw_command_line.decode('UTF-8')
