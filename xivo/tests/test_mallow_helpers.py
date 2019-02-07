# -*- coding: utf-8 -*-
# Copyright 2018-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from collections import OrderedDict
from unittest import TestCase

from hamcrest import (
    assert_that,
    empty,
    has_entries,
    calling,
    raises,
    instance_of,
)
from marshmallow import (
    fields,
    ValidationError,
)

from ..mallow_helpers import ListSchema, Schema


class TestSchema(TestCase):

    def test_ensure_dict(self):
        schema = Schema()

        result, error = schema.load(None)

        assert_that(result, empty())

    def test_strict(self):

        class TestSchema(Schema):

            key = fields.String(required=True)

        assert_that(calling(TestSchema().load).with_args({}),
                    raises(ValidationError))

    def test_ordered(self):

        class TestSchema(Schema):

            key2 = fields.String(required=True)
            key1 = fields.String(required=True)

        result = TestSchema().dump({'key1': '1', 'key2': '2'}).data
        assert_that(result, instance_of(OrderedDict))


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
