# Copyright 2014-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from collections import UserDict
from copy import copy


class ChainMap(UserDict):
    def __init__(self, *dicts):
        self.data = {}
        for d in dicts:
            self.data = self._deep_update(self.data, d)

    def _deep_update(self, original, new):
        updated = copy(original)

        for key, value in new.items():
            if key not in updated:
                updated[key] = copy(value)
            elif isinstance(updated[key], dict) and isinstance(value, dict):
                updated[key] = self._deep_update(updated[key], value)

        return updated


class AccumulatingListChainMap(ChainMap):
    def _deep_update(self, original, new):
        updated = copy(original)

        for key, value in new.items():
            if key not in updated:
                updated[key] = copy(value)
            elif isinstance(updated[key], dict) and isinstance(value, dict):
                updated[key] = self._deep_update(updated[key], value)
            elif isinstance(updated[key], list) and isinstance(value, list):
                updated[key].extend(copy(value))

        return updated
