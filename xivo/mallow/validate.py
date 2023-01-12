# Copyright 2017-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from marshmallow import ValidationError  # noqa: E402
from marshmallow.validate import (  # noqa: E402
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

if TYPE_CHECKING:
    from typing import Any, Dict, TypedDict, Union

    ErrorDict = TypedDict(
        'ErrorDict',
        {
            'message': str,
            'constraint_id': str,
            'constraint': Union[str, Dict[str, Any]],
        },
    )


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
