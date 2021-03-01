# -*- coding: utf-8 -*-
# Copyright 2015-2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import requests
import unittest

from hamcrest import assert_that, calling, equal_to, raises
from mock import Mock, patch, sentinel as s
from ..auth_verifier import (
    AuthServerUnreachable,
    AuthVerifier,
    Unauthorized,
    _ACLCheck,
    no_auth,
    required_acl,
    required_tenant,
)


def function_with_acl(pattern):
    return Mock(acl=_ACLCheck(pattern, None))


class StubVerifier(AuthVerifier):
    def token(self):
        return s.token

    def handle_unreachable(self, error):
        return s.unreachable

    def handle_unauthorized(self, error):
        return s.unauthorized


class TestAuthVerifier(unittest.TestCase):
    def test_set_client(self):
        auth_verifier = AuthVerifier()

        auth_verifier.set_client(s.client)

        assert_that(auth_verifier.client(), equal_to(s.client))

    @patch('xivo.auth_verifier.Client')
    def test_set_config(self, auth_client_init):
        auth_verifier = AuthVerifier()
        config = {
            'host': s.host,
            'username': s.username,
            'password': s.password,
            'key_file': s.key_file,
        }
        expected_config = {'host': s.host}

        auth_verifier.set_config(config)
        auth_verifier.client()

        auth_client_init.assert_called_once_with(**expected_config)

    def test_verify_token_not_configured(self):
        auth_verifier = AuthVerifier()

        @auth_verifier.verify_token
        @required_acl('foo')
        def decorated():
            pass

        assert_that(decorated, raises(RuntimeError))

    def test_verify_tenant_not_configured(self):
        auth_verifier = AuthVerifier()

        @auth_verifier.verify_tenant
        @required_tenant('foo')
        def decorated():
            pass

        assert_that(decorated, raises(RuntimeError))

    def test_verify_token_calls_auth_client(self):
        mock_client = Mock()
        auth_verifier = StubVerifier()
        auth_verifier.set_client(mock_client)

        @auth_verifier.verify_token
        @required_acl('foo')
        def decorated():
            pass

        decorated()

        mock_client.token.is_valid.assert_called_once_with(s.token, 'foo')

    def test_verify_tenant_calls_auth_client(self):
        mock_client = Mock()
        mock_client.token.get.return_value = {'metadata': {'tenant_uuid': ''}}
        auth_verifier = StubVerifier()
        auth_verifier.set_client(mock_client)

        @auth_verifier.verify_tenant
        @required_tenant('foo')
        def decorated():
            pass

        decorated()

        mock_client.token.get.assert_called_once_with(s.token)

    def test_verify_token_calls_function_when_no_auth(self):
        mock_client = Mock()
        mock_client.token.is_valid.return_value = False
        auth_verifier = StubVerifier()
        auth_verifier.set_client(mock_client)

        @auth_verifier.verify_token
        @no_auth
        def decorated():
            return s.result

        result = decorated()

        assert_that(result, equal_to(s.result))
        assert_that(mock_client.token.is_valid.called, equal_to(False))

    def test_verify_token_calls_function_when_valid(self):
        mock_client = Mock()
        mock_client.token.is_valid.return_value = True
        auth_verifier = StubVerifier()
        auth_verifier.set_client(mock_client)

        @auth_verifier.verify_token
        @required_acl('foo')
        def decorated():
            return s.result

        result = decorated()

        assert_that(result, equal_to(s.result))

    def test_verify_tenant_calls_function_when_valid(self):
        mock_client = Mock()
        mock_client.token.get.return_value = {'metadata': {'tenant_uuid': 'foo'}}
        auth_verifier = StubVerifier()
        auth_verifier.set_client(mock_client)

        @auth_verifier.verify_tenant
        @required_tenant('foo')
        def decorated():
            return s.result

        result = decorated()

        assert_that(result, equal_to(s.result))

    def test_verify_token_calls_handle_unreachable(self):
        mock_client = Mock()
        mock_client.token.is_valid.side_effect = requests.RequestException
        auth_verifier = StubVerifier()
        auth_verifier.set_client(mock_client)

        @auth_verifier.verify_token
        @required_acl('foo')
        def decorated():
            return s.result

        result = decorated()

        assert_that(result, equal_to(s.unreachable))

    def test_verify_tenant_calls_handle_unreachable(self):
        mock_client = Mock()
        mock_client.token.get.side_effect = requests.RequestException
        auth_verifier = StubVerifier()
        auth_verifier.set_client(mock_client)

        @auth_verifier.verify_tenant
        @required_tenant('foo')
        def decorated():
            return s.result

        result = decorated()

        assert_that(result, equal_to(s.unreachable))

    def test_verify_token_calls_handle_unauthorized(self):
        mock_client = Mock()
        mock_client.token.is_valid.return_value = False
        auth_verifier = StubVerifier()
        auth_verifier.set_client(mock_client)

        @auth_verifier.verify_token
        @required_acl('foo')
        def decorated():
            return s.result

        result = decorated()

        assert_that(result, equal_to(s.unauthorized))

    def test_verify_tenant_calls_handle_unauthorized(self):
        mock_client = Mock()
        auth_verifier = StubVerifier()
        auth_verifier.set_client(mock_client)

        mock_client.token.get.return_value = {'metadata': {'tenant_uuid': 'bar'}}

        @auth_verifier.verify_tenant
        @required_tenant('foo')
        def decorated():
            return s.result

        result = decorated()

        assert_that(result, equal_to(s.unauthorized))

    @patch('xivo.auth_verifier.request')
    def test_token_empty(self, request):
        request.headers = {}
        auth_verifier = AuthVerifier()

        token = auth_verifier.token()

        assert_that(token, equal_to(''))

    @patch('xivo.auth_verifier.request')
    def test_token_not_empty(self, request):
        request.headers = {'X-Auth-Token': s.token}
        auth_verifier = AuthVerifier()

        token = auth_verifier.token()

        assert_that(token, equal_to(s.token))

    def test_handle_unreachable(self):
        auth_verifier = AuthVerifier()
        auth_verifier.set_config({'host': s.host, 'port': s.port})

        assert_that(
            calling(auth_verifier.handle_unreachable).with_args(None),
            raises(AuthServerUnreachable),
        )

    def test_handle_unauthorized(self):
        auth_verifier = AuthVerifier()

        assert_that(
            calling(auth_verifier.handle_unauthorized).with_args(None),
            raises(Unauthorized),
        )
