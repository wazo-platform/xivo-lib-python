# Copyright 2013-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later


class BaseCommand:
    def prepare(self, command_args):
        return ()

    def execute(self):
        # must be overriden in derived class
        raise NotImplementedError()
