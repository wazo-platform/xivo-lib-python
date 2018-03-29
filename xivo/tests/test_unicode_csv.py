# -*- coding: utf-8 -*-
# Copyright (C) 2013-2016 Avencall
# SPDX-License-Identifier: GPL-3.0+

from hamcrest import assert_that
from hamcrest import equal_to
from hamcrest import instance_of
from hamcrest import only_contains
from six import StringIO, text_type
from unittest import TestCase

from xivo.unicode_csv import UnicodeDictReader, UnicodeDictWriter


class TestUnicodeDictReader(TestCase):

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
            assert_that(result.keys(), only_contains(instance_of(text_type)))
            assert_that(result.values(), only_contains(instance_of(text_type)))

    def test_read_utf8_with_superfluous_fields(self):
        csv_data = ['firstname,lastname', 'Père,Noël,et,son,renne,Léon', 'fírstnámé,lástnámé']
        reader = UnicodeDictReader(csv_data, delimiter=',')
        expected_result = [
            {
                'firstname': u'Père',
                'lastname': u'Noël',
                None: ['et', 'son', 'renne', u'Léon'],
            },
            {
                'firstname': u'fírstnámé',
                'lastname': u'lástnámé'
            }
        ]

        results = [result for result in reader]

        assert_that(results, equal_to(expected_result))

    def test_read_utf8_with_missing_fields(self):
        csv_data = ['firstname,lastname', 'Père', 'fírstnámé,lástnámé']
        reader = UnicodeDictReader(csv_data, delimiter=',')
        expected_result = [
            {
                'firstname': u'Père',
                'lastname': None,
            },
            {
                'firstname': u'fírstnámé',
                'lastname': u'lástnámé'
            }
        ]

        results = [result for result in reader]

        assert_that(results, equal_to(expected_result))


class TestUnicodeDictWriter(TestCase):

    def test_writerow_utf8(self):
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

    def test_writerows_utf8(self):
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

        writer.writerows((first_row, second_row))

        assert_that(result.getvalue(), equal_to(expected_result))
