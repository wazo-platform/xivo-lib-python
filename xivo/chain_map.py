# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Avencall
# SPDX-License-Identifier: GPL-3.0-or-later

from copy import copy

from six import iteritems
from six.moves import UserDict


class ChainMap(UserDict):

    def __init__(self, *dicts):
        self.data = {}
        for d in dicts:
            self.data = self._deep_update(self.data, d)

    def _deep_update(self, original, new):
        updated = copy(original)

        for key, value in iteritems(new):
            if key not in updated:
                updated[key] = copy(value)
            elif isinstance(updated[key], dict) and isinstance(value, dict):
                updated[key] = self._deep_update(updated[key], value)

        return updated
