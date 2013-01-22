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

from __future__ import print_function
from __future__ import unicode_literals


class InputRawCommandLineSource(object):

    def __init__(self, prompt):
        self._prompt = prompt

    def __iter__(self):
        return self

    def next(self):
        while True:
            try:
                raw_command_line = raw_input(self._prompt).decode('UTF-8')
                return raw_command_line
            except EOFError:
                print()
                raise StopIteration()
            except KeyboardInterrupt:
                print('^C')
