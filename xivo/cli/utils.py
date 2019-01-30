# -*- coding: utf-8 -*-
# Copyright (C) 2013-2016 Avencall
# SPDX-License-Identifier: GPL-3.0-or-later

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
            ids.extend(range(int(start), int(end) + 1))
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
