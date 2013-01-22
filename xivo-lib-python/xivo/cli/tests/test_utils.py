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

from __future__ import unicode_literals

import unittest
from xivo.cli.utils import compute_ids


class TestComputeIDs(unittest.TestCase):

    def test_one_id(self):
        self._assertArgId([1], '1')

    def test_two_ids_comma(self):
        self._assertArgId([1, 2], '1,2')

    def test_three_ids_comma(self):
        self._assertArgId([1, 2, 3], '1,2,3')

    def test_id_range(self):
        self._assertArgId([1, 2], '1-2')

    def test_id_range_and_comma(self):
        self._assertArgId([1, 2, 4], '1-2,4')

    def _assertArgId(self, expected, value):
        ids = compute_ids(value)

        self.assertEqual(expected, ids)
