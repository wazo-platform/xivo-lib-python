# -*- coding: utf-8 -*-

# Copyright (C) 2013 Avencall
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

import unittest

from xivo import xivo_helpers


class TestXivoHelpers(unittest.TestCase):

    PREFIX = '_*735.'

    def test_fkey_extension_unc_fwd_with_destination(self):
        arguments = ('123', '_*21.', '1002')

        result = xivo_helpers.fkey_extension(self.PREFIX, arguments)

        self.assertEqual(result, '*735123***221*1002')

    def test_fkey_extension_unc_fwd_without_destination(self):
        arguments = ('123', '_*21.', '')

        result = xivo_helpers.fkey_extension(self.PREFIX, arguments)

        self.assertEqual(result, '*735123***221')

    def test_fkey_extension_dnd(self):
        arguments = ('123', '*25', '')

        result = xivo_helpers.fkey_extension(self.PREFIX, arguments)

        self.assertEqual(result, '*735123***225')
