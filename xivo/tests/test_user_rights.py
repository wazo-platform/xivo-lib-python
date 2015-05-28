# -*- coding: utf-8 -*-

# Copyright (C) 2014-2015 Avencall
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


from mock import Mock, patch
from unittest import TestCase

from .. import user_rights


USER_NAME = 'a_user'
USER_ID = 12
GROUP_ID = 42


@patch('xivo.user_rights.getpwnam')
@patch('os.setuid')
@patch('os.setgid')
class TestChangeUser(TestCase):

    def test_when_user_does_not_exist(self, setgid, setuid, pwnam):
        pwnam.side_effect = KeyError

        self.assertRaises(SystemExit, user_rights.change_user, USER_NAME)

    def test_when_user_exists_but_cannot_change_user(self, setgid, setuid, pwnam):
        pwnam.return_value = Mock(pw_uid=USER_ID)
        setuid.side_effect = OSError

        self.assertRaises(SystemExit, user_rights.change_user, USER_NAME)

        setuid.assert_called_once_with(USER_ID)

    def test_when_success(self, setgid, setuid, pwnam):
        pwnam.return_value = Mock(pw_uid=USER_ID, pw_gid=GROUP_ID)

        user_rights.change_user(USER_NAME)

        pwnam.assert_called_once_with(USER_NAME)
        setuid.assert_called_once_with(USER_ID)
        setgid.assert_called_once_with(GROUP_ID)
