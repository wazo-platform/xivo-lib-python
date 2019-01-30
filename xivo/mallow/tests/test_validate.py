# Copyright 2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from hamcrest import (
    assert_that,
    empty,
    has_entry,
    is_not,
)
from marshmallow import Schema

from .. import fields, validate


class ValidateSchema(Schema):
    string_dict = fields.Dict(validate=validate.validate_string_dict)


class TestValidation(unittest.TestCase):

    def test_given_valid_string_dict_then_validation_works(self):
        data, _ = ValidateSchema().load({'string_dict': {'some': 'str'}})
        assert_that(data, has_entry('string_dict', {'some': 'str'}))

    def test_given_invalid_string_length_then_return_errors(self):
        _, error = ValidateSchema().load({'x'*129: 'x'*2049})
        assert_that(error, is_not(empty))

    def test_given_non_string_values_then_return_errors(self):
        _, error = ValidateSchema().load({1: None})
        assert_that(error, is_not(empty))
