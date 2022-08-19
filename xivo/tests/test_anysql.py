# -*- coding: utf-8 -*-
# Copyright 2022-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
import unittest

from ..anysql import __compare_api_level as compare_api_level


class TestAnySQL(unittest.TestCase):
    def test_compare_api_level(self):
        assert compare_api_level("1.2", "2.1") == -2
        assert compare_api_level("1.2", "2.3") == -2
        assert compare_api_level("2.1", "1.1") == 2
        assert compare_api_level("1.1", "1.1") == 0
