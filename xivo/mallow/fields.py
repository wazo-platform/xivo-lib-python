# Copyright 2017-2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from marshmallow.fields import (
    Boolean,
    DateTime,
    Dict,
    Email,
    Field,
    Integer,
    List,
    Nested,
    String,
    UUID,
)
from . import validate


class _StringifiedDict(dict):

    def format(self, *args, **kwargs):
        self['message'] = self.get('message', '').format(*args, **kwargs)
        return self


class Field(Field):
    default_error_messages = {
        'null': _StringifiedDict(
            message=Field.default_error_messages['null'],
            constraint_id='not_null',
            constraint='not_null'
        ),
        'required': _StringifiedDict(
            message=Field.default_error_messages['required'],
            constraint_id='required',
            constraint='required',
        ),
        'type': _StringifiedDict(
            message=Field.default_error_messages['type'],
            constraint_id='type',
            constraint='type',
        ),
    }


class Boolean(Boolean):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'invalid': _StringifiedDict(
            message=Boolean.default_error_messages['invalid'],
            constraint_id='type',
            constraint='boolean'
        ),
    })


class DateTime(DateTime):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'invalid': _StringifiedDict(
            message=DateTime.default_error_messages['invalid'],
            constraint_id='type',
            constraint='datetime',
        ),
    })


class Dict(Dict):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'invalid': _StringifiedDict(
            message=Dict.default_error_messages['invalid'],
            constraint_id='type',
            constraint='dict',
        ),
    })


class Email(Email):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'invalid': _StringifiedDict(
            message=Email.default_error_messages['invalid'],
            constraint_id='type',
            constraint='email',
        ),
    })


class Integer(Integer):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'invalid': _StringifiedDict(
            message=Integer.default_error_messages['invalid'],
            constraint_id='type',
            constraint='integer',
        ),
    })


class List(List):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'invalid': _StringifiedDict(
            message=List.default_error_messages['invalid'],
            constraint_id='type',
            constraint='list',
        ),
    })


class Nested(Nested):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'type': _StringifiedDict(
            message=Nested.default_error_messages['type'],
            constraint_id='type',
            constraint='dict',
        ),
    })


class String(String):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'invalid': _StringifiedDict(
            message=String.default_error_messages['invalid'],
            constraint_id='type',
            constraint='string',
        ),
    })


class UUID(UUID):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'invalid_uuid': _StringifiedDict(
            message=UUID.default_error_messages['invalid_uuid'],
            constraint_id='type',
            constraint='uuid',
        ),
    })


def WazoOrder(sort_columns, default_sort_column):
    return String(validate=validate.OneOf(sort_columns), missing=default_sort_column)
