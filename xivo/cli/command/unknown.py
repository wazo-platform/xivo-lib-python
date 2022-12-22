# Copyright 2017-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later


from xivo.cli.command.base import BaseCommand


class _BaseUnknownCommand(BaseCommand):

    help = 'Handler for unknown commands'
    usage = None
    _error_msg = None

    def __init__(self, words):
        self._error_msg = f'no such command: {words[0]}'


class PrintingUnknownCommand(_BaseUnknownCommand):
    def execute(self):
        print(self._error_msg)


class RaisingUnknownCommand(_BaseUnknownCommand):
    def execute(self):
        raise Exception(self._error_msg)
