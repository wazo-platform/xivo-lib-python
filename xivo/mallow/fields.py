# Copyright 2017-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

import ipaddress

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

if TYPE_CHECKING:
    from typing import Dict as DictType, TypedDict

    ErrorMessages = TypedDict(
        'ErrorMessages',
        {
            'message': str,
            'constraint_id': str,
            'constraint': str,
        },
    )
    DefaultErrorMessages = DictType[str, Union[ErrorMessages, "_StringifiedDict"]]


class _StringifiedDict(dict):
    def format(self, *args: Any, **kwargs: Any) -> _StringifiedDict:
        self['message'] = self.get('message', '').format(*args, **kwargs)
        return self


class Field(_Field):
    default_error_messages: DefaultErrorMessages = {
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
    default_error_messages: DefaultErrorMessages = dict(Field.default_error_messages)
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
    default_error_messages: DefaultErrorMessages = dict(Field.default_error_messages)
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
    default_error_messages: DefaultErrorMessages = dict(Field.default_error_messages)
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
    default_error_messages: DefaultErrorMessages = dict(Field.default_error_messages)
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
    default_error_messages: DefaultErrorMessages = dict(Field.default_error_messages)
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
    default_error_messages: DefaultErrorMessages = dict(Field.default_error_messages)
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
    default_error_messages: DefaultErrorMessages = dict(Field.default_error_messages)
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
    default_error_messages: DefaultErrorMessages = dict(Field.default_error_messages)
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
    default_error_messages: DefaultErrorMessages = dict(Field.default_error_messages)
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
    default_error_messages: DefaultErrorMessages = dict(Field.default_error_messages)
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
    default_error_messages: DefaultErrorMessages = dict(Field.default_error_messages)
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
    default_error_messages: DefaultErrorMessages = dict(Field.default_error_messages)
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
    default_error_messages: DefaultErrorMessages = dict(Field.default_error_messages)
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
    default_error_messages: DefaultErrorMessages = dict(Field.default_error_messages)


class IP(_String):

    default_error_messages: DefaultErrorMessages = dict(Field.default_error_messages)
    default_error_messages.update(
        {
            'invalid': {
                'message': 'Not a valid IP address.',
                'constraint_id': 'type',
                'constraint': 'ip_address',
            }
        }
    )

    def _deserialize(
        self, value: Any, attr: str | None, data: dict[str, Any], **kwargs: Any
    ) -> str | None:
        deserialized = super()._deserialize(value, attr, data, **kwargs)
        return self._validated(deserialized)

    def _validated(self, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            return str(ipaddress.ip_address(value))
        except ValueError:
            self.fail('invalid')
