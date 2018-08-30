# -*- coding: utf-8 -*-
# Copyright 2015-2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

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

    def test_unsubscribe_from_token_change(self):
        callback = Mock()

        def remove_callback(token):
            self.token_renewer.unsubscribe_from_token_change(callback)

        self.auth_client.token.new.return_value = self.token
        self.token_renewer.subscribe_to_token_change(remove_callback)
        self.token_renewer.subscribe_to_token_change(callback)
        callback.reset_mock()

        self.token_renewer._renew_token()
        callback.assert_called_once_with(self.token_id)
