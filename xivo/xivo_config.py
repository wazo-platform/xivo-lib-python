# -*- coding: utf-8 -*-
# Copyright 2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging

log = logging.getLogger(__name__)


# States for linesubst()
NORM = object()
ONE = object()
TWO = object()
LIT = object()
TLIT = object()
TERM = object()


def linesubst(line, variables):
    """
    In a string, substitute '{{varname}}' occurrences with the value of
    variables['varname'], '\\' being an escaping char...
    If at first you don't understand this function, draw its finite state
    machine and everything will become crystal clear :)
    """
    # trivial no substitution early detection:
    if '{{' not in line and '\\' not in line:
        return line
    st = NORM
    out = ""
    curvar = ""
    for c in line:
        if st is NORM:
            if c == '{':
                st = ONE
            elif c == '\\':
                st = LIT
            else:
                out += c
        elif st is LIT:
            out += c
            st = NORM
        elif st is ONE:
            if c == '{':
                st = TWO
            elif c == '\\':
                out += '{'
                st = LIT
            else:
                out += '{' + c
                st = NORM
        elif st is TWO:
            if c == '\\':
                st = TLIT
            elif c == '}':
                st = TERM
            else:
                curvar += c
        elif st is TLIT:
            curvar += c
            st = TWO
        elif st is TERM:
            if c == '}':
                if curvar not in variables:
                    log.warning(
                        "Unknown variable %r detected, will just be replaced by an empty string",
                        curvar,
                    )
                else:
                    log.debug("Substitution of {{%s}} by %r", curvar, variables[curvar])
                    out += variables[curvar]
                curvar = ''
                st = NORM
            elif c == '\\':
                curvar += '}'
                st = TLIT
            else:
                curvar += '}' + c
                st = TWO
    if st is not NORM:
        log.warning("st is not NORM at end of line: " + line)
        log.warning("returned substitution: " + out)
    return out


def txtsubst(lines, variables, target_file=None, charset=None):
    """
    Log that target_file is going to be generated, and calculate its
    content by applying the linesubst() transformation with the given
    variables to each given lines.
    """
    if target_file:
        log.info("In process of generating file %r", target_file)

    if not charset:
        return [linesubst(line, variables) for line in lines]

    ret = []
    for line in lines:
        linesub = linesubst(line, variables)
        ret.append(linesub)
    return ret
