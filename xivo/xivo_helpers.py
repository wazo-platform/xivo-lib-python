# Copyright 2008-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import re
import sys
import logging

log = logging.getLogger("xivo.xivo_helpers")


find_asterisk_pattern_char = re.compile(r'[\[NXZ!.]').search


def position_of_asterisk_pattern_char(ast_pattern):
    mo = find_asterisk_pattern_char(ast_pattern)
    if not mo:
        return None
    return mo.start()


def clean_extension(exten):
    """
    Return an extension from an Asterisk extension pattern.
    """
    if exten is None:
        return ""

    exten = str(exten)

    if exten.startswith('_'):
        exten = exten[1:]
        e = position_of_asterisk_pattern_char(exten)
        if e is not None:
            exten = exten[:e]

    return exten


def split_extension(exten):
    """
    Return a list of strings that compose the multi parts of an
    extension as to be generated by unsplit_extension().

    >>> split_extension('**142***2666**2***3#**3')
    ('*42', '*666*', '*#*')
    """
    flag = 0
    ret = []
    cur = ""
    i = 1

    if not isinstance(exten, str):
        raise ValueError("exten argument must be a string")

    for x in exten:
        if flag == 2:
            if x.isdigit():
                x = int(x)
                if x == i:
                    flag = 0
                    cur += '*'
                else:
                    raise ValueError("Wrong digit: %d, excepted: %d" % (x, i))
            elif x == '*':
                ret.append(cur)
                cur = ""
                i += 1
            else:
                raise ValueError("Wrong value: %r, excepted digit or asterisk!" % x)
        elif x == '*':
            flag += 1
        elif flag == 1:
            flag = 0
            ret.append(cur)
            cur = x
            i += 1
        else:
            cur += x
    else:
        ret.append(cur)

    return tuple(ret)


def unsplit_extension(xlist):
    """
    Compute and return an extension from multi extensions.

    >>> unsplit_extension(('*98','666'))
    '**198*666'
    """
    ret = []
    cur = ""

    if not isinstance(xlist, (tuple, list)):
        raise ValueError("Argument must be a tuple or list")

    for i, x in enumerate(xlist):
        i += 1
        for c in x:
            if c == '*':
                cur += "**%d" % i
            else:
                cur += c
        else:
            ret.append(cur)
            cur = ""

    return '*'.join(ret)


def fkey_extension(funckey_prefix, funckey_args):
    components = []

    for x in funckey_args:
        x = clean_extension(x)

        if x:
            components.append(x)

    return clean_extension(funckey_prefix) + unsplit_extension(components)


def abort(message, show_tb=False):
    """
    Log @message at critical level (including a backtrace
    if @show_tb is true) then exit.
    """
    log.critical(message, exc_info=show_tb)
    sys.exit(1)
