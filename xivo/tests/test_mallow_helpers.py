# -*- coding: utf-8 -*-
# Copyright 2018-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from unittest import TestCase

from hamcrest import (
    assert_that,
    empty,
    has_entries,
)

from ..mallow_helpers import ListSchema, Schema


class TestSchema(TestCase):

    def test_ensure_dict(self):
        schema = Schema()

        result, error = schema.load(None)

        assert_that(result, empty())


class TestListSchema(TestCase):

    def test_arbitrary_field_search(self):
        schema = ListSchema()
        schema.searchable_columns = ['name']

        raw_data = {
            'name': 'foobar',
            'other': 'foobaz'
        }

        result, error = schema.load(raw_data)

        assert_that(
            result,
            has_entries(name='foobar'),
        )
