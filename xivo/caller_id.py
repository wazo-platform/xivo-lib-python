# Copyright 2012-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import re

COMPLETE_CALLER_ID_PATTERN = re.compile(r'\"(.*)\" \<(\+?\d+)\>')


def is_complete_caller_id(caller_id: str) -> bool:
    return bool(COMPLETE_CALLER_ID_PATTERN.match(caller_id))


def extract_number(caller_id: str) -> str:
    result = COMPLETE_CALLER_ID_PATTERN.search(caller_id)
    if result:
        return result.groups()[1]
    raise ValueError('Not a valid Caller ID: %s', caller_id)


def extract_displayname(caller_id: str) -> str:
    result = COMPLETE_CALLER_ID_PATTERN.search(caller_id)
    if result:
        return result.groups()[0]
    raise ValueError('Not a valid Caller ID: %s', caller_id)


def assemble_caller_id(fullname: str, number: str | None) -> str:
    if number:
        return f'"{fullname}" <{number}>'
    return f'"{fullname}"'
