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

from hamcrest import *
from StringIO import StringIO
from unittest import TestCase
from xivo.unicode_csv import UnicodeDictReader, UnicodeDictWriter


class TestUnicodeDictReader(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_read_utf8(self):
        csv_data = ['firstname,lastname', 'Père,Noël', 'fírstnámé,lástnámé']
        reader = UnicodeDictReader(csv_data, delimiter=',')
        expected_result = [
            {
                'firstname': u'Père',
                'lastname': u'Noël'
            },
            {
                'firstname': u'fírstnámé',
                'lastname': u'lástnámé'
            }
        ]

        results = [result for result in reader]

        assert_that(results, equal_to(expected_result))
        for result in results:
            assert_that(result.keys(), only_contains(instance_of(unicode)))
            assert_that(result.values(), only_contains(instance_of(unicode)))


class TestUnicodeDictWriter(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_write_utf8(self):
        first_row = {
            'firstname': u'Père',
            'lastname': u'Noël'
        }
        second_row = {
            'firstname': u'fírstnámé',
            'lastname': u'lástnámé'
        }
        expected_result = 'Père,Noël\r\nfírstnámé,lástnámé\r\n'
        result = StringIO()
        fieldnames = ['firstname', 'lastname']
        writer = UnicodeDictWriter(result, fieldnames=fieldnames)

        writer.writerow(first_row)
        writer.writerow(second_row)

        assert_that(result.getvalue(), equal_to(expected_result))
