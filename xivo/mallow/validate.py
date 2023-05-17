# Copyright 2017-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import Any, TypedDict
from collections.abc import Sequence

from marshmallow import ValidationError  # noqa: E402
from marshmallow.validate import URL as _URL
from marshmallow.validate import ContainsOnly as _ContainsOnly  # noqa: E402
from marshmallow.validate import Email as _Email
from marshmallow.validate import Equal as _Equal
from marshmallow.validate import Length as _Length
from marshmallow.validate import NoneOf as _NoneOf
from marshmallow.validate import OneOf as _OneOf
from marshmallow.validate import Predicate as _Predicate
from marshmallow.validate import Range as _Range
from marshmallow.validate import Regexp as _Regexp


class ErrorDict(TypedDict):
    message: str
    constraint_id: str
    constraint: str | dict[str, Any]


def validate_string_dict(
    dict_: dict[str, Any], max_key_length: int = 128, max_value_length: int = 2_048
) -> None:
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

    def _format_error(self, value: Sequence[Any]) -> ErrorDict:
        msg = super()._format_error(value)

        return {
            'constraint_id': self.constraint_id,
            'constraint': {'choices': list(self.choices)},
            'message': msg,
        }


class Email(_Email):

    constraint_id = 'email'

    def _format_error(self, value: str | None) -> ErrorDict:
        msg = super()._format_error(value)

        return {
            'constraint_id': self.constraint_id,
            'constraint': 'must be a valid email address',
            'message': msg,
        }


class Equal(_Equal):

    constraint_id = 'equal'

    def _format_error(self, value: Any) -> ErrorDict:
        msg = super()._format_error(value)

        return {
            'constraint_id': self.constraint_id,
            'constraint': {'must_be': self.comparable},
            'message': msg,
        }


class Length(_Length):

    constraint_id = 'length'

    def _format_error(self, value: str | None, message: str) -> ErrorDict:
        msg = super()._format_error(value, message)
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

    def _format_error(self, value: str | None) -> ErrorDict:
        msg = super()._format_error(value)

        return {
            'constraint_id': self.constraint_id,
            'constraint': {'choices': list(self.choices)},
            'message': msg,
        }


class NoneOf(_NoneOf):

    constraint_id = 'ban'

    def _format_error(self, value: str | None) -> ErrorDict:
        msg = super()._format_error(value)

        return {
            'constraint_id': self.constraint_id,
            'constraint': {'bans': self.iterable},
            'message': msg,
        }


class Predicate(_Predicate):

    constraint_id = 'predicate'

    def _format_error(self, value: str | None) -> ErrorDict:
        msg = super()._format_error(value)

        return {
            'constraint_id': self.constraint_id,
            'constraint': {'method': self.method},
            'message': msg,
        }


class Range(_Range):

    constraint_id = 'range'

    def _format_error(self, value: str | None, *args: str | None) -> ErrorDict:
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


class Regexp(_Regexp):

    constraint_id = 'regex'

    def _format_error(self, value: str | None) -> ErrorDict:
        msg = super()._format_error(value)

        return {
            'constraint_id': self.constraint_id,
            'constraint': self.regex.pattern,
            'message': msg,
        }


class URL(_URL):

    constraint_id = 'url'

    def _format_error(self, value: str | None) -> ErrorDict:
        msg = super()._format_error(value)

        return {
            'constraint_id': self.constraint_id,
            'constraint': {'schemes': list(self.schemes)},
            'message': msg,
        }
