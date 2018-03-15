# -*- coding: utf-8 -*-

# Copyright 2016-2018 The Wazo Authors  (see the AUTHORS file)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

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
