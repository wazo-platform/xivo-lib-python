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
import os

from contextlib import contextmanager


@contextmanager
def pidfile(filename):
    try:
        yield add_pid_file(filename)
    except SystemExit:
        pass  # The pidfile should be closed on sys.exit()
    finally:
        remove_pid_file(filename)


def is_already_running(filename):
    return os.path.isfile(filename)


def add_pid_file(filename):
    with open(filename, 'w') as f:
        f.write(str(os.getpid()))


def remove_pid_file(filename):
    try:
        os.unlink(filename)
    except OSError, e:
        if e.errno != errno.ENOENT:
            raise
