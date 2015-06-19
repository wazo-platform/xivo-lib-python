# -*- coding: utf-8 -*-

# Copyright (C) 2014-2015 Avencall
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

from copy import copy
from UserDict import UserDict


class ChainMap(UserDict):

    def __init__(self, *dicts):
        self.data = {}
        for d in dicts:
            self.data = self._deep_update(self.data, d)

    def _deep_update(self, original, new):
        updated = copy(original)

        for key, value in new.iteritems():
            if key not in updated:
                updated[key] = copy(value)
            elif isinstance(updated[key], dict) and isinstance(value, dict):
                updated[key] = self._deep_update(updated[key], value)

        return updated
