# Copyright 2013-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import traceback


class ReRaiseErrorHandler:
    def on_exception(self, e):
        raise


class PrintTracebackErrorHandler:
    def on_exception(self, e):
        traceback.print_exc()
