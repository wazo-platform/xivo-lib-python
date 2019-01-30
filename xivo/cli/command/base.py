# -*- coding: utf-8 -*-
# Copyright (C) 2013-2014 Avencall
# SPDX-License-Identifier: GPL-3.0-or-later


class BaseCommand(object):

    def prepare(self, command_args):
        return ()

    def execute(self):
        # must be overriden in derived class
        raise NotImplementedError()
