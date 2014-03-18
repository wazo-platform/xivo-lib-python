# -*- coding: utf-8 -*-

# Copyright (C) 2013-2014 Avencall
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

import errno
import readline

_HISTORY_LENGTH = 1000


def load(history_file):
    try:
        readline.read_history_file(history_file)
    except IOError as e:
        if e.errno != errno.ENOENT:
            raise


def save(history_file):
    readline.set_history_length(_HISTORY_LENGTH)
    try:
        readline.write_history_file(history_file)
    except IOError as e:
        if e.errno == errno.ENOENT:
            _create_file(history_file)
        else:
            raise


def _create_file(filename):
    with open(filename, 'w'):
        pass
