# Copyright 2013-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import traceback
from typing import NoReturn


class ReRaiseErrorHandler:
    def on_exception(self, e: Exception) -> NoReturn:
        raise


class PrintTracebackErrorHandler:
    def on_exception(self, e: Exception) -> None:
        traceback.print_exc()
