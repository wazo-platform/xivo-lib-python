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

class CommandLineCompleter(object):

    def __init__(self, command_registry):
        self._command_registry = command_registry

    def complete_last_word(self, command_line):
        last_word = command_line.words[-1]
        candidates = self._command_registry.get_next_word(command_line.words[:-1])
        return sorted(candidate for candidate in candidates if candidate.startswith(last_word))

    def complete_next_word(self, command_line):
        candidates = self._command_registry.get_next_word(command_line.words)
        return sorted(candidates)
