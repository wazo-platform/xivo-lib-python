# -*- coding: utf-8 -*-

# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from __future__ import print_function
from __future__ import unicode_literals

from xivo.cli.command.base import BaseCommand


class _BaseUnknownCommand(BaseCommand):

    help = 'Handler for unknown commands'
    usage = None
    _error_msg = None

    def __init__(self, words):
        self._error_msg = 'no such command: {}'.format(words[0])


class PrintingUnknownCommand(_BaseUnknownCommand):

    def execute(self):
        print(self._error_msg)


class RaisingUnknownCommand(_BaseUnknownCommand):

    def execute(self):
        raise Exception(self._error_msg)
