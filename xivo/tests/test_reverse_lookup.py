# Copyright 2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
import unittest

from hamcrest import assert_that, equal_to

from ..reverse_lookup import format_number


class TestReverseLookup(unittest.TestCase):
    def test_valid_numbers(self):
        num1 = '0511223344'
        num2 = '+33511223344'

        num3 = '2507771234'
        num4 = '+12507771234'

        assert_that(format_number(num1, 'FR'), equal_to(num2))
        assert_that(format_number(num2, 'FR'), equal_to(num2))
        assert_that(format_number(num2, None), equal_to(num2))
        assert_that(format_number(num2, 'CA'), equal_to(num2))

        assert_that(format_number(num3, 'CA'), equal_to(num4))
        assert_that(format_number(num4, 'CA'), equal_to(num4))
        assert_that(format_number(num4, None), equal_to(num4))
        assert_that(format_number(num4, 'FR'), equal_to(num4))

    def test_invalid_numbers(self):
        num1 = '18'
        num2 = '911'

        num3 = '0511223344'
        num4 = '2507771234'

        assert_that(format_number(num1, 'FR'), equal_to(None))
        assert_that(format_number(num1, 'CA'), equal_to(None))
        assert_that(format_number(num1, None), equal_to(None))

        assert_that(format_number(num2, 'FR'), equal_to(None))
        assert_that(format_number(num2, 'CA'), equal_to(None))
        assert_that(format_number(num2, None), equal_to(None))

        assert_that(format_number(num3, None), equal_to(None))
        assert_that(format_number(num3, 'CA'), equal_to(None))

        assert_that(format_number(num4, None), equal_to(None))
        assert_that(format_number(num4, 'FR'), equal_to(None))
