# -*- coding: utf-8 -*-
# Copyright 2016-2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import marshmallow

from functools import wraps

from .mallow import fields, validate
from .rest_api_helpers import APIException


class ValidationError(APIException):

    def __init__(self, errors):
        super(ValidationError, self).__init__(
            status_code=400,
            message='Sent data is invalid',
            error_id='invalid-data',
            details=errors
        )


def handle_validation_exception(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except marshmallow.ValidationError as e:
            raise ValidationError(e.messages)
    return wrapper


class ListSchema(marshmallow.Schema):
    default_sort_column = None
    sort_columns = []

    direction = fields.String(validate=validate.OneOf(['asc', 'desc']), missing='asc')
    order = fields.WazoOrder(sort_columns=[], default_sort_column=None)
    limit = fields.Integer(validate=validate.Range(min=0), missing=None)
    offset = fields.Integer(validate=validate.Range(min=0), missing=0)
    search = fields.String(missing=None)

    class Meta:
        strict = True
