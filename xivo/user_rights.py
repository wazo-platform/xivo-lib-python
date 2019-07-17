# -*- coding: utf-8 -*-
# Copyright 2014-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import os

from pwd import getpwnam

from xivo.xivo_helpers import abort


def change_user(user):
    try:
        user = getpwnam(user)
        uid = user.pw_uid
        gid = user.pw_gid
    except KeyError:
        abort('Unknown user {user}'.format(user=user))

    try:
        os.setgid(gid)
        os.initgroups(user.pw_name, gid)
        os.setuid(uid)
    except OSError as e:
        abort(
            'Could not change owner to user {user}: {error}'.format(user=user, error=e)
        )
