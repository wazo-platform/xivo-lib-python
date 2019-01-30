# -*- coding: utf-8 -*-
# Copyright 2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from unittest import TestCase

from hamcrest import (
    assert_that,
    has_entries,
)

from ..mallow_helpers import ListSchema


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
