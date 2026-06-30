# Copyright 2014-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from collections import UserDict
from collections.abc import Mapping
from copy import copy
from typing import Any


class ChainMap(UserDict):
    def __init__(self, *dicts: Mapping[str, Any]) -> None:
        self.data = {}
        for d in dicts:
            self.data = self._deep_update(self.data, d)

    def _deep_update(self, original: dict, new: Mapping[str, Any]) -> dict:
        updated = copy(original)

        for key, value in new.items():
            if key not in updated:
                updated[key] = copy(value)
            elif isinstance(updated[key], dict) and isinstance(value, dict):
                updated[key] = self._deep_update(updated[key], value)

        return updated


class AccumulatingListChainMap(ChainMap):
    def _deep_update(self, original: dict, new: Mapping[str, Any]) -> dict:
        updated = copy(original)

        for key, value in new.items():
            if key not in updated:
                updated[key] = copy(value)
            elif isinstance(updated[key], dict) and isinstance(value, dict):
                updated[key] = self._deep_update(updated[key], value)
            elif isinstance(updated[key], list) and isinstance(value, list):
                updated[key].extend(copy(value))

        return updated
