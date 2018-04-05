# -*- coding: utf-8 -*-
# Copyright 2015-2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import requests
import unittest

from hamcrest import (
    assert_that,
    calling,
    equal_to,
    raises,
)
from mock import (
    Mock,
    patch,
    sentinel as s,
)
from ..auth_verifier import (
    AuthServerUnreachable,
    AuthVerifier,
    Unauthorized,
    _ACLCheck,
    no_auth,
    required_acl,
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
        config = {'host': s.host,
                  'username': s.username,
                  'password': s.password,
                  'key_file': s.key_file}
        expected_config = {'host': s.host}

        auth_verifier.set_config(config)
        auth_verifier.client()

        auth_client_init.assert_called_once_with(**expected_config)

    def test_not_configured(self):
        auth_verifier = AuthVerifier()

        @auth_verifier.verify_token
        @required_acl('foo')
        def decorated():
            pass

        assert_that(decorated, raises(RuntimeError))

    def test_calls_auth_client(self):
        mock_client = Mock()
        auth_verifier = StubVerifier()
        auth_verifier.set_client(mock_client)

        @auth_verifier.verify_token
        @required_acl('foo')
        def decorated():
            pass

        decorated()

        mock_client.token.is_valid.assert_called_once_with(s.token, 'foo')

    def test_calls_function_when_no_auth(self):
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

    def test_calls_function_when_valid(self):
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

    def test_calls_handle_unreachable(self):
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

    def test_calls_handle_unauthorized(self):
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

    def test_acl_empty(self):
        auth_verifier = AuthVerifier()
        mock = Mock()
        del mock.acl

        acl = auth_verifier.acl(mock)

        assert_that(acl, equal_to(''))

    def test_acl_not_empty(self):
        auth_verifier = AuthVerifier()
        function = function_with_acl('{format1},{format2}')

        acl = auth_verifier.acl(function, format1='test1', format2='test2')

        assert_that(acl, equal_to('test1,test2'))

    def test_acl_with_dot(self):
        auth_verifier = AuthVerifier()
        function = function_with_acl('{format1}.{format2}')

        acl = auth_verifier.acl(function, format1='test.1', format2='test.2')

        assert_that(acl, equal_to('test_1.test_2'))

    def test_acl_with_non_str(self):
        auth_verifier = AuthVerifier()
        function = function_with_acl('{format1}.{format2}')

        acl = auth_verifier.acl(function, format1=12, format2=17)

        assert_that(acl, equal_to('12.17'))

    def test_handle_unreachable(self):
        auth_verifier = AuthVerifier()
        auth_verifier.set_config({'host': s.host, 'port': s.port})

        assert_that(calling(auth_verifier.handle_unreachable).with_args(None), raises(AuthServerUnreachable))

    def test_handle_unauthorized(self):
        auth_verifier = AuthVerifier()

        assert_that(calling(auth_verifier.handle_unauthorized).with_args(None), raises(Unauthorized))
