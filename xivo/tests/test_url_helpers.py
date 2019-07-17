# -*- coding: utf-8 -*-
# Copyright 2017-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from hamcrest import assert_that, equal_to
from unittest import TestCase

from ..url_helpers import base_join


class TestURLHelpers(TestCase):
    def test_base_join(self):
        assert_that(base_join('a', 'b', 'c'), equal_to('a/b/c'))
        assert_that(
            base_join('https://example.com', '/b/', '/c/'),
            equal_to('https://example.com/b/c'),
        )
        assert_that(base_join('base', 'abc:def'), equal_to('base/abc%3Adef'))
        assert_that(base_join('base', 123), equal_to('base/123'))
