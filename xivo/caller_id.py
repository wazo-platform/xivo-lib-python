# -*- coding: utf-8 -*-
# Copyright (C) 2012-2014 Avencall
# SPDX-License-Identifier: GPL-3.0+

import re

COMPLETE_CALLER_ID_PATTERN = re.compile('\"(.*)\" \<(\+?\d+)\>')


def build_caller_id(caller_id, name, number):
    if is_complete_caller_id(caller_id):
        cid_name, cid_number = COMPLETE_CALLER_ID_PATTERN.search(caller_id).groups()
        return caller_id, cid_name, cid_number
    else:
        return '"%s" <%s>' % (name, number), name, number


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
