# Copyright 2017-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later


def escape(acl_part):
    return (
        acl_part.replace('.', '__DOT__')
        .replace('#', '__HASH__')
        .replace('*', '__STAR__')
    )
