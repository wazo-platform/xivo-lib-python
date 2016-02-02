# -*- coding: utf-8 -*-

# Copyright (C) 2015-2016 Avencall
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

import unittest

from hamcrest import assert_that
from hamcrest import equal_to
from mock import Mock

from ..token_renewer import TokenRenewer


class TestTokenRenewer(unittest.TestCase):

    def setUp(self):
        self.token_id = 'some-token-id'
        self.token = {'token': self.token_id}
        self.auth_client = Mock()
        self.backend = 'foo-backend'
        self.expiration = 30
        self.token_renewer = TokenRenewer(self.auth_client, self.backend, self.expiration)

    def test_subscribe_to_token_change(self):
        callback = Mock()

        self.token_renewer.subscribe_to_token_change(callback)

        callback.assert_called_once_with(None)

    def test_renew_token_success(self):
        callback = Mock()
        self.auth_client.token.new.return_value = self.token
        self.token_renewer.subscribe_to_token_change(callback)
        callback.reset_mock()

        self.token_renewer._renew_token()

        self.auth_client.token.new.assert_called_once_with(self.backend, expiration=self.expiration)
        callback.assert_called_once_with(self.token_id)

    def test_renew_token_failure(self):
        callback = Mock()
        self.auth_client.token.new.side_effect = Exception()
        self.token_renewer.subscribe_to_token_change(callback)
        callback.reset_mock()

        self.token_renewer._renew_token()

        assert_that(callback.called, equal_to(False))
