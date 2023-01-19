# Copyright 2015-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from unittest.mock import Mock

from hamcrest import assert_that, equal_to

from ..token_renewer import TokenRenewer


class TestTokenRenewer(unittest.TestCase):
    def setUp(self):
        self.token_id = 'some-token-id'
        self.token = {
            'token': self.token_id,
            'metadata': {'uuid': 'some-user', 'tenant_uuid': 'some-tenant'},
        }
        self.auth_client = Mock()
        self.expiration = 30
        self.token_renewer = TokenRenewer(self.auth_client, self.expiration)

    def test_renew_token_success(self):
        callback = Mock()
        self.auth_client.token.new.return_value = self.token
        self.token_renewer.subscribe_to_token_change(callback)
        callback.reset_mock()

        self.token_renewer._renew_token()

        self.auth_client.token.new.assert_called_once_with(expiration=self.expiration)
        callback.assert_called_once_with(self.token_id)

    def test_renew_token_failure(self):
        callback = Mock()
        self.auth_client.token.new.side_effect = Exception()
        self.token_renewer.subscribe_to_token_change(callback)
        callback.reset_mock()

        self.token_renewer._renew_token()

        assert_that(callback.called, equal_to(False))

    def test_subscribe_to_next_token_change(self):
        callback = Mock()
        self.auth_client.token.new.return_value = self.token
        self.token_renewer.subscribe_to_next_token_change(callback)
        callback.reset_mock()

        self.token_renewer._renew_token()

        callback.assert_called_once_with(self.token_id)

        callback.reset_mock()

        self.token_renewer._renew_token()

        callback.assert_not_called()

    def test_subscribe_to_next_token_details_change(self):
        callback = Mock()
        self.auth_client.token.new.return_value = self.token
        self.token_renewer.subscribe_to_next_token_details_change(callback)
        callback.reset_mock()

        self.token_renewer._renew_token()

        callback.assert_called_once_with(self.token)

        callback.reset_mock()

        self.token_renewer._renew_token()

        callback.assert_not_called()
