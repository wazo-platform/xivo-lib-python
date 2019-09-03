# Copyright 2018-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from hamcrest import assert_that, calling, empty, has_entry, has_property, is_not
from marshmallow import Schema, ValidationError

from xivo_test_helpers.hamcrest.raises import raises

from .. import fields


class AllFieldsSchema(Schema):
    string = fields.String()
    integer = fields.Integer()
    float_ = fields.Float()
    boolean = fields.Integer()
    date = fields.Date()
    datetime = fields.DateTime()
    dict_ = fields.Dict()
    email = fields.Email()
    list_ = fields.List(fields.String())
    nested = fields.Nested('TestSchema')
    uuid = fields.UUID()
    constant = fields.Constant('constant')
    ip = fields.IP()


class TestFields(unittest.TestCase):
    def test_when_not_dict_object_then_no_crash_occurs(self):
        assert_that(
            calling(AllFieldsSchema().load).with_args(1),
            raises(ValidationError, has_property('messages', is_not(empty()))),
        )

    def test_when_invalid_email_then_no_crash_occurs(self):
        assert_that(
            calling(AllFieldsSchema().load).with_args({'email': 'invalid_email'}),
            raises(ValidationError, has_property('messages', is_not(empty()))),
        )

    def test_given_valid_ipv4_then_validation_works(self):
        data = AllFieldsSchema().load({'ip': '127.0.0.1'})
        assert_that(data, has_entry('ip', '127.0.0.1'))

    def test_given_valid_ipv6_then_validation_works(self):
        data = AllFieldsSchema().load({'ip': '::'})
        assert_that(data, has_entry('ip', '::'))

    def test_given_invalid_ipv4_then_return_errors(self):
        assert_that(
            calling(AllFieldsSchema().load).with_args({'ip': '999.999.999.999'}),
            raises(ValidationError, has_property('messages', is_not(empty()))),
        )

    def test_given_invalid_ipv6_then_return_errors(self):
        # IPv6 addresses may not contains :: twice
        invalid_ipv6 = '1200::AB00:1234::2552:7777:1313'
        assert_that(
            calling(AllFieldsSchema().load).with_args({'ip': invalid_ipv6}),
            raises(ValidationError, has_property('messages', is_not(empty()))),
        )
