# Copyright 2018-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from hamcrest import (
    assert_that,
    calling,
    contains,
    empty,
    has_entries,
    has_entry,
    has_property,
    is_not,
)
from marshmallow import Schema, ValidationError

from xivo_test_helpers.hamcrest.raises import raises


from .. import fields, validate


class ValidateSchema(Schema):
    string_dict = fields.Dict(validate=validate.validate_string_dict)


class TestValidation(unittest.TestCase):
    def test_given_valid_string_dict_then_validation_works(self):
        data = ValidateSchema().load({'string_dict': {'some': 'str'}})
        assert_that(data, has_entry('string_dict', {'some': 'str'}))

    def test_given_invalid_string_length_then_return_errors(self):
        assert_that(
            calling(ValidateSchema().load).with_args(
                {'string_dict': {'x' * 129: 'x' * 2049}}
            ),
            raises(ValidationError, has_property('messages', is_not(empty))),
        )

    def test_given_non_string_values_then_return_errors(self):
        assert_that(
            calling(ValidateSchema().load).with_args({'string_dict': {1: None}}),
            raises(ValidationError, has_property('messages', is_not(empty))),
        )


class LengthSchema(Schema):
    equal = fields.String(validate=validate.Length(equal=2))
    min_max = fields.String(validate=validate.Length(min=2, max=3))


class TestLengthValidation(unittest.TestCase):
    def test_length_equal(self):
        assert_that(
            calling(LengthSchema().load).with_args({'equal': 'a'}),
            raises(
                ValidationError,
                has_property(
                    'messages',
                    has_entry('equal', contains(has_entries(constraint={'equal': 2}))),
                ),
            ),
        )

    def test_length_min_max(self):
        assert_that(
            calling(LengthSchema().load).with_args({'min_max': 'a'}),
            raises(
                ValidationError,
                has_property(
                    'messages',
                    has_entry(
                        'min_max',
                        contains(has_entries(constraint={'min': 2, 'max': 3})),
                    ),
                ),
            ),
        )
