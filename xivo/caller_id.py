# Copyright 2012-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import re

COMPLETE_CALLER_ID_PATTERN = re.compile(r'\"(.*)\" \<(\+?\d+)\>')


def is_complete_caller_id(caller_id):
    return bool(COMPLETE_CALLER_ID_PATTERN.match(caller_id))


def extract_number(caller_id):
    result = COMPLETE_CALLER_ID_PATTERN.search(caller_id)
    if result:
        return result.groups()[1]
    else:
        raise ValueError('Not a valid Caller ID: %s', caller_id)


def extract_displayname(caller_id):
    result = COMPLETE_CALLER_ID_PATTERN.search(caller_id)
    if result:
        return result.groups()[0]
    else:
        raise ValueError('Not a valid Caller ID: %s', caller_id)


def assemble_caller_id(fullname, number):
    if number:
        return '"%s" <%s>' % (fullname, number)
    return '"%s"' % fullname
