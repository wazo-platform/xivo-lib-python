# -*- coding: utf-8 -*-

# Copyright (C) 2013-2014 Avencall
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

from hamcrest import assert_that, equal_to
from xivo import caller_id
from xivo.caller_id import build_caller_id, is_complete_caller_id, extract_number, \
    extract_displayname


class TestCallerID(unittest.TestCase):

    def test_caller_id_no_num(self):
        begin = '"User One"'
        name = 'User One'
        number = '123'

        cid_all, cid_name, cid_number = build_caller_id(begin, name, number)

        self.assertEqual(cid_all, '"%s" <%s>' % (name, number))
        self.assertEqual(cid_name, name)
        self.assertEqual(cid_number, number)

    def test_caller_id_number(self):
        begin = '"User One" <123>'
        name = 'User One'
        number = '123'

        cid_all, cid_name, cid_number = build_caller_id(begin, name, number)

        self.assertEqual(cid_all, '"%s" <%s>' % (name, number))
        self.assertEqual(cid_name, name)
        self.assertEqual(cid_number, number)

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

        assert_that(result, equal_to('"%s" <%s>' % (fullname, number)))

    def test_assemble_caller_id_without_extension(self):
        fullname = 'User 1'
        number = None

        result = caller_id.assemble_caller_id(fullname, number)

        assert_that(result, equal_to('"%s"' % fullname))
