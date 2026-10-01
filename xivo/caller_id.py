# Copyright 2012-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import re

COMPLETE_CALLER_ID_PATTERN = re.compile(r'\"(.*)\" \<(\+?\d+)\>')

# What the dialplan accepts as a caller ID: a name, quoted or not, optionally
# followed by a number in angle brackets. A name alone that looks like a number
# is also the number.
CALLER_ID_PATTERN = re.compile(
    r'^ *(?:"(.+)"|([\w\-\.\!%\*\+`\'\~ ]*[^ "])) *(?:<(\+?[0-9\*#]+)>)?$'
)
CALLER_ID_NUMBER_PATTERN = re.compile(r'^\+?[0-9\*#]+$')


def is_complete_caller_id(caller_id: str) -> bool:
    return bool(COMPLETE_CALLER_ID_PATTERN.match(caller_id))


def extract_number(caller_id: str) -> str:
    if match := COMPLETE_CALLER_ID_PATTERN.search(caller_id):
        return match.groups()[1]
    raise ValueError('Not a valid Caller ID: %s', caller_id)


def extract_displayname(caller_id: str) -> str:
    if match := COMPLETE_CALLER_ID_PATTERN.search(caller_id):
        return match.groups()[0]
    raise ValueError('Not a valid Caller ID: %s', caller_id)


def assemble_caller_id(fullname: str, number: str | None) -> str:
    if number:
        return f'"{fullname}" <{number}>'
    return f'"{fullname}"'


def parse_caller_id(caller_id: str | None) -> tuple[str, str | None] | None:
    '''
    split a caller ID into (name, number), or return None when the dialplan
    could not parse it. A bare number is both the name and the number.
    '''
    if not caller_id or not (match := CALLER_ID_PATTERN.match(caller_id)):
        return None

    quoted_name, unquoted_name, number = match.groups()
    if quoted_name is not None:
        return quoted_name, number
    if number is None and CALLER_ID_NUMBER_PATTERN.match(unquoted_name):
        return unquoted_name, unquoted_name
    return unquoted_name, number


def is_valid_caller_id(caller_id: str) -> bool:
    return parse_caller_id(caller_id) is not None
