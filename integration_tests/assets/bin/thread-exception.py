#!/usr/bin/env python3
# Copyright 2018-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import threading
import time
from typing import NoReturn

from xivo import xivo_logging

xivo_logging.setup_logging('/dev/null')


def failure() -> NoReturn:
    raise RuntimeError('If you see this, then the exception is logged!')


threading.Thread(target=failure).start()

while True:
    time.sleep(1)
