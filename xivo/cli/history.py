# Copyright 2013-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

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
