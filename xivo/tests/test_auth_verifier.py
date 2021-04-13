# -*- coding: utf-8 -*-
# Copyright 2015-2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import requests
import unittest

from hamcrest import assert_that, calling, equal_to, raises
from mock import Mock, patch, sentinel as s
from ..auth_verifier import (
    AccessCheck,
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


class TestAccessCheck(unittest.TestCase):
    def test_matches_required_access_when_user_access_ends_with_hashtag(self):
        access_check = AccessCheck('123', 'session-uuid', ['foo.bar.#'])

        assert_that(access_check.matches_required_access('foo.bar'), equal_to(False))
        assert_that(access_check.matches_required_access('foo.bar.toto'))
        assert_that(access_check.matches_required_access('foo.bar.toto.tata'))
        assert_that(
            access_check.matches_required_access('other.bar.toto'), equal_to(False)
        )

    def test_matches_required_access_when_user_access_has_not_special_character(self):
        access_check = AccessCheck('123', 'session-uuid', ['foo.bar.toto'])

        assert_that(access_check.matches_required_access('foo.bar.toto'))
        assert_that(
            access_check.matches_required_access('foo.bar.toto.tata'), equal_to(False)
        )
        assert_that(
            access_check.matches_required_access('other.bar.toto'), equal_to(False)
        )

    def test_matches_required_access_when_user_access_has_asterisks(self):
        access_check = AccessCheck('123', 'session-uuid', ['foo.*.*'])

        assert_that(access_check.matches_required_access('foo.bar.toto'))
        assert_that(
            access_check.matches_required_access('foo.bar.toto.tata'), equal_to(False)
        )
        assert_that(
            access_check.matches_required_access('other.bar.toto'), equal_to(False)
        )

    def test_matches_required_access_with_multiple_accesses(self):
        access_check = AccessCheck(
            '123', 'session-uuid', ['foo', 'foo.bar.toto', 'other.#']
        )

        assert_that(access_check.matches_required_access('foo'))
        assert_that(access_check.matches_required_access('foo.bar'), equal_to(False))
        assert_that(access_check.matches_required_access('foo.bar.toto'))
        assert_that(
            access_check.matches_required_access('foo.bar.toto.tata'), equal_to(False)
        )
        assert_that(access_check.matches_required_access('other.bar.toto'))

    def test_matches_required_access_when_user_access_has_hashtag_in_middle(self):
        access_check = AccessCheck('123', 'session-uuid', ['foo.bar.#.titi'])

        assert_that(access_check.matches_required_access('foo.bar'), equal_to(False))
        assert_that(
            access_check.matches_required_access('foo.bar.toto'), equal_to(False)
        )
        assert_that(
            access_check.matches_required_access('foo.bar.toto.tata'), equal_to(False)
        )
        assert_that(access_check.matches_required_access('foo.bar.toto.tata.titi'))

    def test_matches_required_access_when_user_access_ends_with_me(self):
        access_check = AccessCheck('123', 'session-uuid', ['foo.#.me'])

        assert_that(access_check.matches_required_access('foo.bar'), equal_to(False))
        assert_that(access_check.matches_required_access('foo.bar.me'), equal_to(True))
        assert_that(access_check.matches_required_access('foo.bar.123'))
        assert_that(access_check.matches_required_access('foo.bar.toto.me'))
        assert_that(access_check.matches_required_access('foo.bar.toto.123'))
        assert_that(
            access_check.matches_required_access('foo.bar.toto.me.titi'),
            equal_to(False),
        )
        assert_that(
            access_check.matches_required_access('foo.bar.toto.123.titi'),
            equal_to(False),
        )

    def test_matches_required_access_when_user_access_has_me_in_middle(self):
        access_check = AccessCheck('123', 'session-uuid', ['foo.#.me.bar'])

        assert_that(
            access_check.matches_required_access('foo.bar.123'), equal_to(False)
        )
        assert_that(access_check.matches_required_access('foo.bar.me'), equal_to(False))
        assert_that(access_check.matches_required_access('foo.bar.123.bar'))
        assert_that(
            access_check.matches_required_access('foo.bar.me.bar'), equal_to(True)
        )
        assert_that(access_check.matches_required_access('foo.bar.toto.123.bar'))
        assert_that(access_check.matches_required_access('foo.bar.toto.me.bar'))

    def test_does_not_match_required_access_when_negating(self):
        access_check = AccessCheck('123', 'session-uuid', ['!foo.me.bar'])

        assert_that(access_check.matches_required_access('foo.me.bar'), equal_to(False))

    def test_does_not_match_required_access_when_negating_multiple_identical_accesses(
        self,
    ):
        access_check = AccessCheck(
            '123', 'session-uuid', ['foo.me.bar', '!foo.me.bar', 'foo.me.bar']
        )

        assert_that(access_check.matches_required_access('foo.me.bar'), equal_to(False))

    def test_does_not_match_required_access_when_negating_ending_hashtag(self):
        access_check = AccessCheck(
            '123', 'session-uuid', ['!foo.me.bar.#', 'foo.me.bar.123']
        )

        assert_that(
            access_check.matches_required_access('foo.me.bar.123'), equal_to(False)
        )

    def test_does_not_match_required_access_when_negating_hashtag_sublevel(self):
        access_check = AccessCheck(
            '123', 'session-uuid', ['foo.#', '!foo.me.bar.#', 'foo.me.bar.123']
        )

        assert_that(
            access_check.matches_required_access('foo.me.bar.123'), equal_to(False)
        )

    def test_matches_required_access_when_negating_specific(self):
        access_check = AccessCheck('123', 'session-uuid', ['foo.*.bar', '!foo.123.bar'])

        assert_that(access_check.matches_required_access('foo.me.bar'))
        assert_that(
            access_check.matches_required_access('foo.123.bar'), equal_to(False)
        )

    def test_does_not_match_required_access_when_negating_toplevel(self):
        access_check = AccessCheck('123', 'session-uuid', ['!*.bar', 'foo.bar'])

        assert_that(access_check.matches_required_access('foo.bar'), equal_to(False))

    def test_matches_my_session(self):
        access_check = AccessCheck('123', 'session-uuid', ['foo.my_session'])

        assert_that(access_check.matches_required_access('foo.session-uuid'))
        assert_that(access_check.matches_required_access('foo.my_session'))
        assert_that(
            access_check.matches_required_access('foo.another-session-uuid'),
            equal_to(False),
        )
