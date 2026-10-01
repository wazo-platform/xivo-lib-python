# Copyright 2013-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from hamcrest import assert_that, equal_to

from xivo import caller_id
from xivo.caller_id import (
    extract_displayname,
    extract_number,
    is_complete_caller_id,
    is_valid_caller_id,
    parse_caller_id,
)


class TestCallerID(unittest.TestCase):
    def test_is_complete_caller_id(self):
        cid = '"User One" <1234>'

        self.assertTrue(is_complete_caller_id(cid))

    def test_is_complete_caller_id_false(self):
        cid = '1234'

        self.assertFalse(is_complete_caller_id(cid))

    def test_extract_number(self):
        caller_id = '"User 1" <1001>'

        ret = extract_number(caller_id)

        self.assertEqual(ret, '1001')

    def test_extract_number_leading_plus(self):
        caller_id = '"User 1" <+1001>'

        ret = extract_number(caller_id)

        self.assertEqual(ret, '+1001')

    def test_extract_number_not_a_caller_id(self):
        self.assertRaises(ValueError, extract_number, '1001')

    def test_extract_displayname(self):
        caller_id = '"User 1" <1001>'

        ret = extract_displayname(caller_id)

        self.assertEqual(ret, 'User 1')

    def test_extract_displayname_with_invalid_caller_id(self):
        self.assertRaises(ValueError, extract_displayname, '1001')

    def test_assemble_caller_id_with_extension(self):
        fullname = 'User 1'
        number = '2345'

        result = caller_id.assemble_caller_id(fullname, number)

        assert_that(result, equal_to(f'"{fullname}" <{number}>'))

    def test_assemble_caller_id_without_extension(self):
        fullname = 'User 1'
        number = None

        result = caller_id.assemble_caller_id(fullname, number)

        assert_that(result, equal_to(f'"{fullname}"'))


class TestParseCallerID(unittest.TestCase):
    def test_parse(self):
        test_cases = (
            ('Test <123>', ('Test', '123')),
            ('"Test" <+123>', ('Test', '+123')),
            ('"Test <+123>', None),
            ('Test" <+123>', None),
            ('"Test word   " <+123>', ('Test word   ', '+123')),
            ('Test2 word    <+123>', ('Test2 word', '+123')),
            ('Test3 word    <123>', ('Test3 word', '123')),
            ('  Test4 word    <123>', ('Test4 word', '123')),
            ('"Acme Corp" <*12#>', ('Acme Corp', '*12#')),
            ('a', ('a', None)),
            ('1', ('1', '1')),
            ('+123', ('+123', '+123')),
            ('anonymous', ('anonymous', None)),
            ('default', ('default', None)),
            ('"" <123>', None),
            ('<123>', None),
            ('Bad; name <123>', None),
            ('', None),
            (None, None),
        )
        for test_case, expected_result in test_cases:
            assert_that(
                parse_caller_id(test_case), equal_to(expected_result), test_case
            )

    def test_is_valid_caller_id(self):
        assert_that(is_valid_caller_id('"Acme Corp" <+14185551234>'), equal_to(True))
        assert_that(is_valid_caller_id('+14185551234'), equal_to(True))
        assert_that(is_valid_caller_id('<+14185551234>'), equal_to(False))
        assert_that(is_valid_caller_id(''), equal_to(False))
