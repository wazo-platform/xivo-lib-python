# -*- coding: utf-8 -*-
# Copyright (C) 2013-2014 Avencall
# SPDX-License-Identifier: GPL-3.0+

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
