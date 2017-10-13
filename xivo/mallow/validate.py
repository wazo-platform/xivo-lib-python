# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from marshmallow.validate import Email
from marshmallow.validate import Equal
from marshmallow.validate import Length
from marshmallow.validate import OneOf
from marshmallow.validate import Predicate
from marshmallow.validate import Range
from marshmallow.validate import Regexp
from marshmallow.validate import URL


class Email(Email):

    constraint_id = 'email'

    def _format_error(self, value):
        msg = super(Email, self)._format_error(value)

        return {
            'constraint_id': self.constraint_id,
            'constraint': 'must be a valid email address',
            'message': msg,
        }


class Equal(Equal):

    constraint_id = 'equal'

    def _format_error(self, value):
        msg = super()._format_error(value)

        return {
            'constraint_id': self.constraint_id,
            'constraint': {'must_be': self.comparable},
            'message': msg,
        }


class Length(Length):

    constraint_id = 'length'

    def _format_error(self, value, message):
        msg = super(Length, self)._format_error(value, message)

        return {
            'constraint_id': self.constraint_id,
            'constraint': {'min': self.min, 'max': self.max},
            'message': msg,
        }


class OneOf(OneOf):

    constraint_id = 'enum'

    def _format_error(self, value):
        msg = super()._format_error(value)

        return {
            'constraint_id': self.constraint_id,
            'constraint': {'choices': self.choices},
            'message': msg,
        }


class Predicate(Predicate):

    constraint_id = 'predicate'

    def _format_error(self, value):
        msg = super()._format_error(value)

        return {
            'constraint_id': self.constraint_id,
            'constraint': {'method': self.method},
            'message': msg,
        }


class Range(Range):

    constraint_id = 'range'

    def _format_error(self, value, *args):
        msg = super()._format_error(value, *args)
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


class Regexp(Regexp):

    constraint_id = 'regex'

    def _format_error(self, value):
        msg = super()._format_error(value)

        return {
            'constraint_id': self.constraint_id,
            'constraint': self.regex.pattern,
            'message': msg,
        }


class URL(URL):

    constraint_id = 'url'

    def _format_error(self, value):
        msg = super()._format_error(value)

        return {
            'constraint_id': self.constraint_id,
            'constraint': {'schemes': list(self.schemes)},
            'message': msg,
        }
