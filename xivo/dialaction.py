# Copyright 2021-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later


def action(type_, subtype=None):
    type_ = type_ or ''
    subtype = f':{subtype}' if subtype else ''
    return f'{type_}{subtype}'


def action_type(action):
    return action.split(':', 1)[0] if action else None


def action_subtype(action):
    type_subtype = action.split(':', 1) if action else ''
    return type_subtype[1] if len(type_subtype) == 2 else None
