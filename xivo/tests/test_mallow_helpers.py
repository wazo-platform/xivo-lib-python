# Copyright 2018-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from collections import OrderedDict
import unittest

from hamcrest import (
    all_of,
    assert_that,
    empty,
    has_entries,
    has_key,
    has_property,
    calling,
    instance_of,
    not_,
)
from marshmallow import fields, ValidationError
from wazo_test_helpers.hamcrest.raises import raises

from ..mallow_helpers import ListSchema, Schema


class TestSchema(unittest.TestCase):
    def test_ensure_dict(self):
        schema = Schema()

        result = schema.load(None)

        assert_that(result, empty())

    def test_strict(self):
        class TestSchema(Schema):
            key = fields.String(required=True)

        assert_that(calling(TestSchema().load).with_args({}), raises(ValidationError))

    def test_ordered(self):
        class TestSchema(Schema):
            key2 = fields.String(required=True)
            key1 = fields.String(required=True)

        result = TestSchema().dump({'key1': '1', 'key2': '2'})
        assert_that(result, instance_of(OrderedDict))


class TestListSchema(unittest.TestCase):
    def test_arbitrary_field_search(self):
        class Schema(ListSchema):
            searchable_columns = ['name']

        raw_data = {'name': 'foobar', 'other': 'foobaz'}

        result = Schema().load(raw_data)

        assert_that(result, all_of(has_entries(name='foobar'), not_(has_key('other'))))

    def test_order_sort_columns(self):
        class Schema(ListSchema):
            sort_columns = ['name']

        raw_data = {'order': 'name'}

        result = Schema().load(raw_data)

        assert_that(result, has_entries(order='name'))

    def test_order_sort_columns_error(self):
        class Schema(ListSchema):
            sort_columns = ['name']

        raw_data = {'order': 'other-columns'}

        assert_that(
            calling(Schema().load).with_args(raw_data),
            raises(ValidationError, has_property('messages', has_key('order'))),
        )

    def test_order_default_sort_column(self):
        class Schema(ListSchema):
            default_sort_column = 'name'
            sort_columns = ['name']

        result = Schema().load({})

        assert_that(result, has_entries(order='name'))

    def test_direction_default_direction(self):
        class Schema(ListSchema):
            default_direction = 'desc'

        result = Schema().load({})

        assert_that(result, has_entries(direction='desc'))

    def test_default_values(self):
        result = ListSchema().load({})

        assert_that(
            result,
            has_entries(direction='asc', order=None, limit=None, offset=0, search=None),
        )
