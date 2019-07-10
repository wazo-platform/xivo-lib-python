# -*- coding: utf-8 -*-
# Copyright 2013-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import traceback


class ReRaiseErrorHandler(object):
    def on_exception(self, e):
        raise


class PrintTracebackErrorHandler(object):
    def on_exception(self, e):
        traceback.print_exc()
