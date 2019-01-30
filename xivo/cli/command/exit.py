# -*- coding: utf-8 -*-
# Copyright (C) 2013-2014 Avencall
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import unicode_literals

from xivo.cli.command.base import BaseCommand


class ExitCommand(BaseCommand):

    help = 'Exit the interpreter'
    usage = None

    def execute(self):
        raise SystemExit()
