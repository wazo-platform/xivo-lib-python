# Copyright 2017-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import sys

python_major_version = sys.version_info.major
if python_major_version < 3:
    raise ImportError(
        'Marshamallow library is incompatible with Python version {version}'.format(
            version=sys.version
        )
    )

from marshmallow.fields import (  # noqa: E402
    Boolean as _Boolean,
    Constant as _Constant,
    Date as _Date,
    DateTime as _DateTime,
    Dict as _Dict,
    Email as _Email,
    Field as _Field,
    Float as _Float,
    Integer as _Integer,
    List as _List,
    Nested as _Nested,
    String as _String,
    TimeDelta as _TimeDelta,
    URL as _URL,
    UUID as _UUID,
)

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
            constraint='not_null',
        ),
        'required': _StringifiedDict(
            message=_Field.default_error_messages['required'],
            constraint_id='required',
            constraint='required',
        ),
    }


class Boolean(_Boolean):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update(
        {
            'invalid': _StringifiedDict(
                message=_Boolean.default_error_messages['invalid'],
                constraint_id='type',
                constraint='boolean',
            )
        }
    )


class Date(_Date):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update(
        {
            'invalid': _StringifiedDict(
                message=_Date.default_error_messages['invalid'],
                constraint_id='type',
                constraint='date',
            )
        }
    )


class DateTime(_DateTime):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update(
        {
            'invalid': _StringifiedDict(
                message='Not a valid datetime',
                constraint_id='type',
                constraint='datetime',
            )
        }
    )


class Dict(_Dict):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update(
        {
            'invalid': _StringifiedDict(
                message=_Dict.default_error_messages['invalid'],
                constraint_id='type',
                constraint='dict',
            )
        }
    )


class Email(_Email):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update(
        {
            'invalid': _StringifiedDict(
                message=_Email.default_error_messages['invalid'],
                constraint_id='type',
                constraint='email',
            )
        }
    )


class Integer(_Integer):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update(
        {
            'invalid': _StringifiedDict(
                message=_Integer.default_error_messages['invalid'],
                constraint_id='type',
                constraint='integer',
            )
        }
    )


class Float(_Float):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update(
        {
            'special': _StringifiedDict(
                message=_Float.default_error_messages['special'],
                constraint_id='type',
                constraint='float',
            )
        }
    )


class List(_List):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update(
        {
            'invalid': _StringifiedDict(
                message=_List.default_error_messages['invalid'],
                constraint_id='type',
                constraint='list',
            )
        }
    )


class Nested(_Nested):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update(
        {
            'type': _StringifiedDict(
                message=_Nested.default_error_messages['type'],
                constraint_id='type',
                constraint='dict',
            )
        }
    )


class String(_String):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update(
        {
            'invalid': _StringifiedDict(
                message=_String.default_error_messages['invalid'],
                constraint_id='type',
                constraint='string',
            )
        }
    )


class TimeDelta(_TimeDelta):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update(
        {
            'invalid': _StringifiedDict(
                message=_TimeDelta.default_error_messages['invalid'],
                constraint_id='type',
                constraint='timedelta',
            ),
            'format': _StringifiedDict(
                message='Cannot be formatted as a timedelta',
                constraint_id='type',
                constraint='format',
            ),
        }
    )


class URL(_URL):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update(
        {
            'invalid_url': _StringifiedDict(
                message=_URL.default_error_messages['invalid'],
                constraint_id='type',
                constraint='url',
            )
        }
    )


class UUID(_UUID):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update(
        {
            'invalid_uuid': _StringifiedDict(
                message=_UUID.default_error_messages['invalid_uuid'],
                constraint_id='type',
                constraint='uuid',
            )
        }
    )


class Constant(_Constant):
    default_error_messages = dict(Field.default_error_messages)


class IP(_String):

    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update(
        {
            'invalid': {
                'message': 'Not a valid IP address.',
                'constraint_id': 'type',
                'constraint': 'ip_address',
            }
        }
    )

    def __init__(self, *args, **kwargs):
        if not ipaddress_available:
            raise RuntimeError('IP field requires the python ipaddress library')
        super(IP, self).__init__(*args, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        deserialized = super(IP, self)._deserialize(value, attr, data, **kwargs)
        return self._validated(deserialized)

    def _validated(self, value):
        if value is None:
            return None
        try:
            return str(ipaddress.ip_address(value))
        except ValueError:
            self.fail('invalid')
