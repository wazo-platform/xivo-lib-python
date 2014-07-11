# -*- coding: utf-8 -*-

# Copyright (C) 2014 Avencall
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

import os

from pwd import getpwnam

from xivo.xivo_helpers import abort


def change_user(user):
    try:
        uid = getpwnam(user).pw_uid
    except KeyError:
        abort('Unknown user {user}'.format(user=user))

    try:
        os.setuid(uid)
    except OSError as e:
        abort('Could not change owner to user {user}: {error}'.format(user=user, error=e))
