# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from marshmallow.fields import Field
from marshmallow.fields import Boolean
from marshmallow.fields import DateTime
from marshmallow.fields import Dict
from marshmallow.fields import Email
from marshmallow.fields import List
from marshmallow.fields import Integer
from marshmallow.fields import Nested
from marshmallow.fields import String
from marshmallow.fields import UUID
from . import validate


class Field(Field):
    default_error_messages = {
        'null': {'message': Field.default_error_messages['null'],
                 'constraint_id': 'not_null',
                 'constraint': 'not_null'},
        'required': {'message': Field.default_error_messages['required'],
                     'constraint_id': 'required',
                     'constraint': 'required'},
        'type': {'message': Field.default_error_messages['type'],
                 'constraint_id': 'type',
                 'constraint': 'type'},
    }


class Boolean(Boolean):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'invalid': {'message': Boolean.default_error_messages['invalid'],
                    'constraint_id': 'type',
                    'constraint': 'boolean'},
    })


class DateTime(DateTime):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'invalid': {'message': DateTime.default_error_messages['invalid'],
                    'constraint_id': 'type',
                    'constraint': 'datetime'},
    })


class Dict(Dict):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'invalid': {'message': Dict.default_error_messages['invalid'],
                    'constraint_id': 'type',
                    'constraint': 'dict'},
    })


class Email(Email):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'invalid': {'message': Email.default_error_messages['invalid'],
                    'constraint_id': 'type',
                    'constraint': 'email'},
    })

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        # the default implementation does not work well with "invalid" being a dict
        self.validators[0] = validate.Email()


class Integer(Integer):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'invalid': {'message': Integer.default_error_messages['invalid'],
                    'constraint_id': 'type',
                    'constraint': 'integer'},
    })


class List(List):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'invalid': {'message': List.default_error_messages['invalid'],
                    'constraint_id': 'type',
                    'constraint': 'list'},
    })


class Nested(Nested):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'type': {'message': Nested.default_error_messages['type'],
                 'constraint_id': 'type',
                 'constraint': 'dict'},
    })


class String(String):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'invalid': {'message': String.default_error_messages['invalid'],
                    'constraint_id': 'type',
                    'constraint': 'string'},
    })


class UUID(UUID):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'invalid_uuid': {'message': UUID.default_error_messages['invalid_uuid'],
                         'constraint_id': 'type',
                         'constraint': 'uuid'},
    })
