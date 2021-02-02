# Copyright 2017-2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from marshmallow import ValidationError
from marshmallow.validate import (
    ContainsOnly as _ContainsOnly,
    Email as _Email,
    Equal as _Equal,
    Length as _Length,
    OneOf as _OneOf,
    NoneOf as _NoneOf,
    Predicate as _Predicate,
    Range as _Range,
    Regexp as _Regexp,
    URL as _URL,
)


def validate_string_dict(dict_, max_key_length=128, max_value_length=2048):
    for key, value in dict_.items():
        if not (isinstance(key, str) and isinstance(value, str)):
            raise ValidationError(
                {
                    'message': 'Not a mapping with string keys and string values',
                    'constraint_id': 'key-value-type',
                    'constraint': 'string',
                }
            )
        if len(key) > max_key_length or len(value) > max_value_length:
            raise ValidationError(
                {
                    'message': 'Key or value too long',
                    'constraint_id': 'key-value-length',
                    'constraint': {
                        'key-max': max_key_length,
                        'value-max': max_value_length,
                    },
                }
            )


class ContainsOnly(_ContainsOnly):

    constraint_id = 'enum'

    def _format_error(self, value):
        msg = super(ContainsOnly, self)._format_error(value)

        return {
            'constraint_id': self.constraint_id,
            'constraint': {'choices': list(self.choices)},
            'message': msg,
        }


class Email(_Email):

    constraint_id = 'email'

    def _format_error(self, value):
        msg = super(Email, self)._format_error(value)

        return {
            'constraint_id': self.constraint_id,
            'constraint': 'must be a valid email address',
            'message': msg,
        }


class Equal(_Equal):

    constraint_id = 'equal'

    def _format_error(self, value):
        msg = super(Equal, self)._format_error(value)

        return {
            'constraint_id': self.constraint_id,
            'constraint': {'must_be': self.comparable},
            'message': msg,
        }


class Length(_Length):

    constraint_id = 'length'

    def _format_error(self, value, message):
        msg = super(Length, self)._format_error(value, message)
        if self.equal:
            constraint = {'equal': self.equal}
        else:
            constraint = {'min': self.min, 'max': self.max}

        return {
            'constraint_id': self.constraint_id,
            'constraint': constraint,
            'message': msg,
        }


class OneOf(_OneOf):

    constraint_id = 'enum'

    def _format_error(self, value):
        msg = super(OneOf, self)._format_error(value)

        return {
            'constraint_id': self.constraint_id,
            'constraint': {'choices': list(self.choices)},
            'message': msg,
        }


class NoneOf(_NoneOf):

    constraint_id = 'ban'

    def _format_error(self, value):
        msg = super(NoneOf, self)._format_error(value)

        return {
            'constraint_id': self.constraint_id,
            'constraint': {'bans': self.iterable},
            'message': msg,
        }


class Predicate(_Predicate):

    constraint_id = 'predicate'

    def _format_error(self, value):
        msg = super(Predicate, self)._format_error(value)

        return {
            'constraint_id': self.constraint_id,
            'constraint': {'method': self.method},
            'message': msg,
        }


class Range(_Range):

    constraint_id = 'range'

    def _format_error(self, value, *args):
        msg = super(Range, self)._format_error(value, *args)
        constraint = {}
        if self.min is not None:
            constraint['min'] = self.min
        if self.max is not None:
            constraint['max'] = self.max

        return {
            'constraint_id': self.constraint_id,
            'constraint': constraint,
            'message': msg,
        }


class Regexp(_Regexp):

    constraint_id = 'regex'

    def _format_error(self, value):
        msg = super(Regexp, self)._format_error(value)

        return {
            'constraint_id': self.constraint_id,
            'constraint': self.regex.pattern,
            'message': msg,
        }


class URL(_URL):

    constraint_id = 'url'

    def _format_error(self, value):
        msg = super(URL, self)._format_error(value)

        return {
            'constraint_id': self.constraint_id,
            'constraint': {'schemes': list(self.schemes)},
            'message': msg,
        }
