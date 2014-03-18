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

from __future__ import unicode_literals

import functools
from xivo.cli.exception import UsageError


def compute_ids(command_arg):
    ids = []
    for id_item in command_arg.split(','):
        start, sep, end = id_item.partition('-')
        if not sep:
            ids.append(int(id_item))
        else:
            ids.extend(xrange(int(start), int(end) + 1))
    return ids


def wraps_error_as_usage_error(fun):
    @functools.wraps(fun)
    def aux(*args, **kwargs):
        try:
            return fun(*args, **kwargs)
        except UsageError:
            raise
        except Exception:
            raise UsageError()
    return aux
