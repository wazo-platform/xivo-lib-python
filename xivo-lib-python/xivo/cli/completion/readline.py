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
        command_line = self._raw_command_line_parser.parse(raw_command_line)
        if text:
            self._candidates = self._command_line_completer.complete_last_word(command_line)
        else:
            self._candidates = self._command_line_completer.complete_next_word(command_line)

        if len(self._candidates) == 1:
            self._candidates[0] += self._raw_command_line_parser.word_delimiter

    def _get_raw_command_line(self):
        line_buffer = readline.get_line_buffer()
        end_idx = readline.get_endidx()
        raw_command_line = line_buffer[:end_idx]
        return raw_command_line.decode('UTF-8')
