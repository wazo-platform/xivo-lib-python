# -*- coding: utf-8 -*-
# Copyright 2013-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later


class BaseCommand(object):
    def prepare(self, command_args):
        return ()

    def execute(self):
        # must be overriden in derived class
        raise NotImplementedError()
