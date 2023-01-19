# Copyright 2016-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from functools import wraps  # noqa: E402
import marshmallow  # noqa: E402

from .mallow import fields, validate  # noqa: E402
from .rest_api_helpers import APIException  # noqa: E402


class ValidationError(APIException):
    def __init__(self, errors):
        super().__init__(
            status_code=400,
            message='Sent data is invalid',
            error_id='invalid-data',
            details=errors,
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
    default_sort_column: str | None = None
    sort_columns: list[str] = []
    searchable_columns: list[str] = []
    default_direction = 'asc'

    direction = fields.String(validate=validate.OneOf(['asc', 'desc']))
    order = fields.String()
    limit = fields.Integer(validate=validate.Range(min=0), missing=None)
    offset = fields.Integer(validate=validate.Range(min=0), missing=0)
    search = fields.String(missing=None)

    class Meta:
        unknown = marshmallow.EXCLUDE

    def on_bind_field(self, field_name, field_obj):
        if field_name == 'order':
            self._set_order_parameters(field_obj)
        elif field_name == 'direction':
            self._set_direction_parameters(field_obj)

    def _set_direction_parameters(self, field_obj):
        field_obj.missing = self.default_direction

    def _set_order_parameters(self, field_obj):
        field_obj.validators = [validate.OneOf(self.sort_columns)]
        field_obj.missing = self.default_sort_column
        if self.default_sort_column is None:
            field_obj.allow_none = True
        else:
            field_obj.allow_none = False

    @marshmallow.post_load(pass_original=True)
    def add_searchable_fields(self, data, original_data, **kwargs):
        for key, value in original_data.items():
            if key in self.searchable_columns:
                data.setdefault(key, value)

        return data


class Schema(marshmallow.Schema):
    class Meta:
        ordered = True
        unknown = marshmallow.EXCLUDE

    @marshmallow.pre_load
    def ensure_dict(self, data, **kwargs):
        return data or {}
