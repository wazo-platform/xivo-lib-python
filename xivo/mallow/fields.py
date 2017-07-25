# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from marshmallow.fields import Field
from marshmallow.fields import Boolean
from marshmallow.fields import Dict
from marshmallow.fields import List
from marshmallow.fields import Integer
from marshmallow.fields import Nested
from marshmallow.fields import String


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


class Dict(Dict):
    default_error_messages = dict(Field.default_error_messages)
    default_error_messages.update({
        'invalid': {'message': Dict.default_error_messages['invalid'],
                    'constraint_id': 'type',
                    'constraint': 'dict'},
    })


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
