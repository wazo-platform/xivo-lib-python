# -*- coding: utf-8 -*-

# Copyright (C) 2012-2013 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import re

COMPLETE_CALLER_ID_PATTERN = re.compile('\"(.*)\" \<(\d+)\>')


def build_caller_id(caller_id, name, number):
    if _complete_caller_id(caller_id):
        cid_name, cid_number = COMPLETE_CALLER_ID_PATTERN.search(caller_id).groups()
        return caller_id, cid_name, cid_number
    else:
        return '"%s" <%s>' % (name, number), name, number


def _complete_caller_id(caller_id):
    return True if COMPLETE_CALLER_ID_PATTERN.match(caller_id) else False


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
