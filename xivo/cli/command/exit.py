# Copyright 2013-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later


from xivo.cli.command.base import BaseCommand


class ExitCommand(BaseCommand):

    help = 'Exit the interpreter'
    usage = None

    def execute(self):
        raise SystemExit()
