# -*- coding: utf-8 -*-
# Copyright (C) 2013-2014 Avencall
# SPDX-License-Identifier: GPL-3.0+

import traceback


class ReRaiseErrorHandler(object):

    def on_exception(self, e):
        raise


class PrintTracebackErrorHandler(object):

    def on_exception(self, e):
        traceback.print_exc()
