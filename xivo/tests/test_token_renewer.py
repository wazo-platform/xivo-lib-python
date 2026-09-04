# Copyright 2015-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from unittest.mock import Mock

import requests
from hamcrest import assert_that, equal_to, has_item, has_property, not_

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

    def test_renew_token_gateway_error_logs_without_traceback(self):
        self.auth_client.token.new.side_effect = self._http_error(502)

        with self.assertLogs('xivo.token_renewer', level='DEBUG') as logs:
            self.token_renewer._renew_token()

        assert_that(logs.records, not_(has_item(has_property('exc_info', not_(None)))))

    def test_renew_token_other_http_error_logs_traceback(self):
        self.auth_client.token.new.side_effect = self._http_error(401)

        with self.assertLogs('xivo.token_renewer', level='DEBUG') as logs:
            self.token_renewer._renew_token()

        assert_that(logs.records, has_item(has_property('exc_info', not_(None))))

    def _http_error(self, status_code):
        response = Mock(status_code=status_code)
        return requests.exceptions.HTTPError(
            f'{status_code} Server Error', response=response
        )

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
