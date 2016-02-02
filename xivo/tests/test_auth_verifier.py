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

import requests
import unittest

from hamcrest import assert_that
from hamcrest import calling
from hamcrest import equal_to
from hamcrest import raises
from mock import Mock
from mock import patch
from mock import sentinel as s

from ..auth_verifier import AuthServerUnreachable
from ..auth_verifier import AuthVerifier
from ..auth_verifier import Unauthorized


class StubVerifier(AuthVerifier):

    def token(self):
        return s.token

    def acl(self, decorated_function, *args, **kwargs):
        return s.acl

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
        def decorated():
            pass

        assert_that(decorated, raises(AssertionError))

    def test_calls_auth_client(self):
        mock_client = Mock()
        auth_verifier = StubVerifier()
        auth_verifier.set_client(mock_client)

        @auth_verifier.verify_token
        def decorated():
            pass

        decorated()

        mock_client.token.is_valid.assert_called_once_with(s.token, s.acl)

    def test_calls_function_when_valid(self):
        mock_client = Mock()
        mock_client.token.is_valid.return_value = True
        auth_verifier = StubVerifier()
        auth_verifier.set_client(mock_client)

        @auth_verifier.verify_token
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
        mock = Mock(acl='{format1},{format2}')

        acl = auth_verifier.acl(mock, format1='test1', format2='test2')

        assert_that(acl, equal_to('test1,test2'))

    def test_handle_unreachable(self):
        auth_verifier = AuthVerifier()
        auth_verifier.set_config({'host': s.host, 'port': s.port})

        assert_that(calling(auth_verifier.handle_unreachable).with_args(None), raises(AuthServerUnreachable))

    def test_handle_unauthorized(self):
        auth_verifier = AuthVerifier()

        assert_that(calling(auth_verifier.handle_unauthorized).with_args(None), raises(Unauthorized))
