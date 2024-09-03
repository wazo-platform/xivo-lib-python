# Copyright 2013-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import errno
import readline

_HISTORY_LENGTH = 1_000


def load(history_file: str) -> None:
    try:
        readline.read_history_file(history_file)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def save(history_file: str) -> None:
    readline.set_history_length(_HISTORY_LENGTH)
    try:
        readline.write_history_file(history_file)
    except OSError as e:
        if e.errno == errno.ENOENT:
            _create_file(history_file)
        else:
            raise


def _create_file(filename: str) -> None:
    with open(filename, 'w'):
        pass
