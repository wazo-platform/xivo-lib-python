# Copyright 2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import unittest

from hamcrest import (
    assert_that,
    empty,
    is_not,
)
from marshmallow import Schema

from .. import fields


class AllFieldsSchema(Schema):
    string = fields.String()
    integer = fields.Integer()
    boolean = fields.Integer()
    datetime = fields.DateTime()
    dict_ = fields.Dict()
    email = fields.Email()
    list_ = fields.List(fields.String())
    nested = fields.Nested('TestSchema')
    uuid = fields.UUID()


class TestStringifiedDict(unittest.TestCase):

    def test_when_not_dict_object_then_no_crash_occurs(self):
        _, error = AllFieldsSchema().load(1)
        assert_that(error, is_not(empty))

    def test_when_invalid_email_then_no_crash_occurs(self):
        _, error = AllFieldsSchema().load({'email': 'invalid_email'})
        assert_that(error, is_not(empty))
