# -*- coding: utf-8 -*-
# Copyright 2008-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Interworking with udev

NOTE: based on udev-105 internals (Debian Etch)
WARNING: Linux specific module - and maybe even Debian specific module
"""

import re
import subprocess
from copy import deepcopy
import logging


log = logging.getLogger("xivo.udev")  # pylint: disable-msg=C0103


UDEVTRIGGER = "/sbin/udevtrigger"


def find(seq, f):
    """
    Return the first element el of seq for which f(el) is true, or
    None if f(el) is not true for each elements of seq.
    """
    for el in seq:
        if f(el):
            return el


def is_comment(mline):
    """
    Return True if @mline is a comment, else False.
    """
    return mline[:1] == "#"


def iter_multilines(lines):
    """
    Iterate over @lines and yield the multilines they form.  A multiline
    stops only on a "\\n" (newline) that is not preceded with a "\\\\"
    (backslash) or at end of file.  "\\\\\\n" of continued lines are
    stripped, as well as regular "\\n" at end of multilines and spaces at
    their beginning.  Comment lines and blank lines are not skipped.
    """
    current = []
    for line in lines:
        if line[-2:] == "\\\n":
            current.append(line[:-2])
        else:
            if line[-1:] == "\n":
                current.append(line[:-1])
            else:
                current.append(line)
            yield ''.join(current).lstrip()
            current = []
    if current:
        yield ''.join(current).lstrip()


RULE_KEY_REO = re.compile(r'([\s,]*)(.+?)(\s*)(==|!=|\+=|=|:=)(\s*)"(.*?)"(.*)$')

# WARNING: the following positions are 0 based - not for use in a call to mo.group()
RULE_KEY_POS_KEY = 1
RULE_KEY_POS_OP = 3
RULE_KEY_POS_VAL = 5


OP_ALL = ('==', '!=', '+=', '=', ':=')
OP_MATCH_NOMATCH = ('==', '!=')


KEY_ATTR = {
    # key in file: (key in dict, allowed operations)
    'ATTR': ('ATTR', OP_ALL),
    'ATTRS': ('ATTRS', OP_ALL),
    'SYSFS': ('ATTRS', OP_ALL),
    'ENV': ('ENV', OP_ALL),
}


KEY_OPT_ATTR = ('IMPORT', 'NAME')


KEY = {
    # key in file: (key in dict, allowed operations)
    'ACTION': ('ACTION', OP_MATCH_NOMATCH),
    'DEVPATH': ('DEVPATH', OP_MATCH_NOMATCH),
    'KERNEL': ('KERNEL', OP_MATCH_NOMATCH),
    'SUBSYSTEM': ('SUBSYSTEM', OP_MATCH_NOMATCH),
    'DRIVER': ('DRIVER', OP_MATCH_NOMATCH),
    'KERNELS': ('KERNELS', OP_MATCH_NOMATCH),
    'ID': ('KERNELS', OP_MATCH_NOMATCH),
    'SUBSYSTEMS': ('SUBSYSTEMS', OP_MATCH_NOMATCH),
    'BUS': ('SUBSYSTEMS', OP_MATCH_NOMATCH),
    'DRIVERS': ('DRIVERS', OP_MATCH_NOMATCH),
    'PROGRAM': ('PROGRAM', OP_ALL),
    'RESULT': ('RESULT', OP_MATCH_NOMATCH),
    'IMPORT': ('IMPORT', OP_ALL),
    'RUN': ('RUN', OP_ALL),
    'WAIT_FOR_SYSFS': ('WAIT_FOR_SYSFS', OP_ALL),
    'LABEL': ('LABEL', OP_ALL),
    'GOTO': ('GOTO', OP_ALL),
    'NAME': ('NAME', OP_ALL),
    'SYMLINK': ('SYMLINK', OP_ALL),
    'OWNER': ('OWNER', OP_ALL),
    'GROUP': ('GROUP', OP_ALL),
    'MODE': ('MODE', OP_ALL),
    'OPTIONS': ('OPTIONS', OP_ALL),
}


KEY_WITH_ATTR_REO = re.compile(r'([^{]+)\{([^}]*)\}')


def base_attr_key(key):
    """
    If "{" not in key:
        return key, None.
    If "{" in key:
        key must be in the form base + "{" + attr + "}"
        where key is non empty and attr can be empty.
            (otherwise raise a ValueError)
        return base, attr
    """
    if "{" not in key:
        return key, None
    match_key_attr = KEY_WITH_ATTR_REO.match(key)
    if match_key_attr is None:
        raise ValueError("invalid key: %r" % key)
    return match_key_attr.groups()


def base_attr_strip_opt(key):
    """
    Behave as base_attr_key(), except when the @base result is a key in
    @KEY_OPT_ATTR: in this case return base, None

    REM: base_attr_key() can raise a ValueError, so base_attr_strip_opt()
    can raise a ValueError too.
    """
    base, attr = base_attr_key(key)
    if base in KEY_OPT_ATTR:
        return base, None
    else:
        return base, attr


def parse_rule(mline):
    """
    Parse @mline quite like add_to_rules() does in udev.

    If the rule is syntaxically invalid, this function returns None.
    If the rule is not too much syntaxically invalid, this function
    returns (rule, reconstructible_rule).

    @rule is a dictionary with the following structure:
    { key_attr_1: { attr_1: [op_1, val_1],
                    attr_2: [op_2, val_2],
                    ... },
      ...,
      key_3: [op_3, val_3],
      ... }
    where @key_attr_{n} is an element of the "key in dict" column of
    @KEY_ATTR, @attr_{p} can be any string, @op_{q} is an udev rule
    operator in ('==', '!=', '+=', '=', ':='), @val_{r} can be any string,
    and @key_{s} is an element of the "key in dict" column of @KEY.

    @reconstructible_rule is a list with the following structure:
    [elem, ...]
    where @elem is a list of the first subgroups as they are in
    @RULE_KEY_REO (the last subgroup is the "rest of the line" and is
    parsed using the same regex until it does not match)
    @reconstructible_rule store even the unrecognized keys, so when the
    line is reconstructed using it it is possible to avoid unnecessary
    changes.

    NOTE: the "key in dict" columns are a subset of the keys of @KEY or
    @KEY_ATTR and the sets are disjoint.
    """
    rule = {}
    reconstructible_rule = []

    # rotl: rest of the line
    rotl = mline

    while True:
        match_key_subpart = RULE_KEY_REO.match(rotl)
        if not match_key_subpart:
            break
        sep, key, spc_1, op, spc_2, val, rotl = match_key_subpart.groups()
        reconstructible_rule.append([sep, key, spc_1, op, spc_2, val])

        try:
            base, attr = base_attr_strip_opt(key)
        except ValueError:
            log.error("parse_rule: unclosed attribute in %r", key)
            return None

        # key with attribute?
        if attr is not None:
            if base in KEY_ATTR:
                rule_key, rule_allowed_ops = KEY_ATTR[base]
                if op not in rule_allowed_ops:
                    log.error(
                        "parse_rule: invalid rule multiline %r (invalid operation %r for key %r)",
                        mline,
                        op,
                        key,
                    )
                    return None
                rule.setdefault(rule_key, {})
                rule[rule_key][attr] = [op, val]
            else:
                log.warning("parse_rule: unknown key %r", key)
                continue

        # Simple key
        if base in KEY:
            rule_key, rule_allowed_ops = KEY[base]
            if op not in rule_allowed_ops:
                log.error(
                    "parse_rule: invalid rule multiline %r (invalid operation %r for key %r)",
                    mline,
                    op,
                    key,
                )
                return None
            rule[rule_key] = [op, val]
        else:
            log.warning("parse_rule: unknown key %r", key)

    # next line is magic logic taken from udev_rules_parse.c:add_to_rules()
    valid = len(rule) >= 2 or (len(rule) == 1 and "NAME" not in rule)
    if not valid:
        log.error("parse_rule: invalid rule multiline %r", mline)
        return None

    return rule, reconstructible_rule


def match_rule(rule, match):
    """
    @rule: Parsed udev rule.  See format in parse_rule() pydoc.
    @match: Dictionary (see format in parse_rule() pydoc)
            There will be a match iff for each key of @match, a
            corresponding key exists in @rule with the same value in both.
    """
    for key, value in match.iteritems():
        if key not in rule:
            return False
        if rule[key] != value:
            return False
    else:
        return True


def reconstruct_rule_elem(elem):
    """
    Reconstruct a slice of a rule string.
    Used by reconstruct_rule()
    """
    return '%s%s%s%s%s"%s"' % tuple(elem)


def reconstruct_rule(recons):
    """
    Return a string which when parsed by parse_rule() results in @recons.
    """
    return "".join((reconstruct_rule_elem(elem) for elem in recons))


def replace_simple_op_values(recons, repl):
    """
    @recons is a list in the format of @reconstructible_rule described in
    pydoc of parse_rule().

    This function returns a reconstructed rule line in which operations and
    values are replaced by using those of @repl for each corresponding key.

    WARNING: only works for keys in @KEY
    """
    modified_recons = deepcopy(recons)

    for subpart in modified_recons:
        key = subpart[RULE_KEY_POS_KEY]
        base, attr = base_attr_strip_opt(key)
        if attr is not None:
            continue
        if base in repl:
            repl_op, repl_val = repl[base]
            rule_allowed_ops = KEY[base][1]
            if repl_op not in rule_allowed_ops:
                raise ValueError(
                    "invalid replacement operation %r for key %r in rule %r"
                    % (repl_op, key, reconstruct_rule(recons))
                )
            if '"' in repl_val:
                raise ValueError(
                    "illegal character %r in replacement value %r for key %r in rule %r"
                    % ('"', repl_val, key, reconstruct_rule(recons))
                )
            subpart[RULE_KEY_POS_OP] = repl_op
            subpart[RULE_KEY_POS_VAL] = repl_val

    return reconstruct_rule(modified_recons)


def replace_simple(lines, match_repl_lst):
    """
    Transform @lines (generate the output) by doing some replacement in
    rules according to @match_repl_lst.

    @match_repl_lst: [(match, repl), ...]
    @match: Dictionary (see format in parse_rule() pydoc)
            There will be a match iff for each key of @match, a
            corresponding key exists in the parsed rule with the same
            value.
    @repl: Dictionary (see format in parse_rule() pydoc)
           When there is a match, this dictionary is used to replace
           entries of the matching rule.
           You can only use simple entries in this dictionary (in the form
           @key_{s} described in parse_rule() pydoc; possible keys are
           listed in @KEY).

    WARNING: There will be no continued line in output; any line which was
    continued in input will be transformed into its non-continued
    equivalent.  Also lines will be left stripped.
    """
    for mline in iter_multilines(lines):
        if (not mline) or is_comment(mline):
            yield mline + "\n"
            continue

        rule_recons = parse_rule(mline)
        if not rule_recons:
            yield mline + "\n"
            continue

        match_repl = find(
            match_repl_lst, (lambda mr: match_rule(rule_recons[0], mr[0]))
        )
        if match_repl is None:
            yield mline + "\n"
            continue

        repl = match_repl[1]
        yield replace_simple_op_values(rule_recons[1], repl) + "\n"


class TriggerError(Exception):
    "udevtrigger invocation/failure error"


def trigger():
    """
    Call udevtrigger
    """
    try:
        status = subprocess.call([UDEVTRIGGER], close_fds=True)
    except OSError:
        log.exception("could not invoke udevtrigger")
        raise TriggerError("could not invoke udevtrigger")
    if status != 0:
        raise TriggerError("udevtrigger failed")
