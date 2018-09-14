# Copyright 2017-2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from marshmallow.fields import (
    Boolean as _Boolean,
    Date as _Date,
    DateTime as _DateTime,
    Dict as _Dict,
    Email as _Email,
    Field as _Field,
    Integer as _Integer,
    List as _List,
    Nested as _Nested,
    String as _String,
    UUID as _UUID,
    ValidatedField,
)
from . import validate

ipaddress_available = True
try:
    import ipaddress  # stdlib in python3, needs to be installed in python2
except ImportError:
    ipaddress_available = False


class _StringifiedDict(dict):

    def format(self, *args, **kwargs):
        self['message'] = self.get('message', '').format(*args, **kwargs)
        return self


class Field(_Field):
    default_error_messages = {
        'null': _StringifiedDict(
            message=_Field.default_error_messages['null'],
            constraint_id='not_null',
            constraint='not_null'
        ),
        'required': _StringifiedDict(
            message=_Field.default_error_messages['required'],
            constraint_id='required',
            constraint='required',
        ),
        'type': _StringifiedDict(
            message=_Field.default_error_messages['type'],
            constraint_id='type',
            constraint='type',
        ),
    }


class Boolean(_Boolean):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'invalid': _StringifiedDict(
            message=_Boolean.default_error_messages['invalid'],
            constraint_id='type',
            constraint='boolean'
        ),
    })


class Date(_Date):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'invalid': _StringifiedDict(
            message=_Date.default_error_messages['invalid'],
            constraint_id='type',
            constraint='date',
        ),
    })


class DateTime(_DateTime):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'invalid': _StringifiedDict(
            message=_DateTime.default_error_messages['invalid'],
            constraint_id='type',
            constraint='datetime',
        ),
    })


class Dict(_Dict):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'invalid': _StringifiedDict(
            message=_Dict.default_error_messages['invalid'],
            constraint_id='type',
            constraint='dict',
        ),
    })


class Email(_Email):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'invalid': _StringifiedDict(
            message=_Email.default_error_messages['invalid'],
            constraint_id='type',
            constraint='email',
        ),
    })


class Integer(_Integer):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'invalid': _StringifiedDict(
            message=_Integer.default_error_messages['invalid'],
            constraint_id='type',
            constraint='integer',
        ),
    })


class List(_List):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'invalid': _StringifiedDict(
            message=_List.default_error_messages['invalid'],
            constraint_id='type',
            constraint='list',
        ),
    })


class Nested(_Nested):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'type': _StringifiedDict(
            message=_Nested.default_error_messages['type'],
            constraint_id='type',
            constraint='dict',
        ),
    })


class String(_String):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'invalid': _StringifiedDict(
            message=_String.default_error_messages['invalid'],
            constraint_id='type',
            constraint='string',
        ),
    })


class UUID(_UUID):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'invalid_uuid': _StringifiedDict(
            message=_UUID.default_error_messages['invalid_uuid'],
            constraint_id='type',
            constraint='uuid',
        ),
    })


class IP(ValidatedField, String):

    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'invalid': {'message': 'Not a valid IP address.',
                    'constraint_id': 'type',
                    'constraint': 'ip_address'},
    })

    def __init__(self, *args, **kwargs):
        if not ipaddress_available:
            raise RuntimeError('IP field requires the python ipaddress library')
        super().__init__(*args, **kwargs)

    def _validated(self, value):
        if value is None:
            return None
        try:
            return str(ipaddress.ip_address(value))
        except ValueError:
            self.fail('invalid')


def WazoOrder(sort_columns, default_sort_column):
    return String(validate=validate.OneOf(sort_columns), missing=default_sort_column)
