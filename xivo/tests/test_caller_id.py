# Copyright 2013-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from hamcrest import assert_that, equal_to
from xivo import caller_id
from xivo.caller_id import is_complete_caller_id, extract_number, extract_displayname


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

        assert_that(result, equal_to('"%s"' % fullname))
