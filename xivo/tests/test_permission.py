# -*- coding: utf-8 -*-
# Copyright 2017-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from hamcrest import assert_that
from hamcrest import equal_to
from hamcrest import is_not

from ..permission import escape


class TestEscape(unittest.TestCase):
    def test_escape(self):
        assert_that(escape('my-id'), equal_to('my-id'))
        assert_that(escape('my.id'), is_not(equal_to('my.id')))
        assert_that(escape('my#id'), is_not(equal_to('my#id')))
        assert_that(escape('my*id'), is_not(equal_to('my*id')))
