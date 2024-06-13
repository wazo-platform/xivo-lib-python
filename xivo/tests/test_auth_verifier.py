# Copyright 2015-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from unittest.mock import Mock, patch
from unittest.mock import sentinel as s

import pytest
import requests
from hamcrest import assert_that, calling, equal_to, is_, raises
from wazo_auth_client.exceptions import (
    InvalidTokenException,
    MissingPermissionsTokenException,
)

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

    def handle_unauthorized(self, error, required_access=None):
        return s.unauthorized

    def _handle_invalid_token_exception(self, error, required_access=None):
        return s.invalid_token

    def _handle_missing_permissions_token_exception(self, error, required_access=None):
        return s.missing_permission


class TestAuthVerifier(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('xivo.auth_verifier.request', Mock())
        self.request_mock = self.patcher.start()
        del self.request_mock.token_id
        del self.request_mock._token_content
        del self.request_mock.user_uuid

    def tearDown(self):
        self.patcher.stop()

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

        mock_client.token.check.assert_called_once_with(s.token, 'foo')

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
        mock_client.token.check.side_effect = MissingPermissionsTokenException
        auth_verifier = StubVerifier()
        auth_verifier.set_client(mock_client)

        @auth_verifier.verify_token
        @no_auth
        def decorated():
            return s.result

        result = decorated()

        assert_that(result, equal_to(s.result))

    def test_verify_token_with_no_acl_permission_raises_exception(self):
        mock_client = Mock()
        mock_client.token.check.side_effect = MissingPermissionsTokenException
        auth_verifier = StubVerifier()
        auth_verifier.set_client(mock_client)

        @auth_verifier.verify_token
        @required_acl('confd')
        def decorated():
            return s.result

        result = decorated()

        assert_that(result, equal_to(s.missing_permission))

    def test_verify_token_calls_function_when_valid(self):
        mock_client = Mock()
        mock_client.token.check.return_value = True
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
        mock_client.token.check.side_effect = requests.RequestException
        auth_verifier = StubVerifier()
        auth_verifier.set_client(mock_client)

        @auth_verifier.verify_token
        @required_acl('foo')
        def decorated():
            return s.result

        result = decorated()

        assert_that(result, equal_to(s.unreachable))

    def test_verify_token_sets_the_token_id_on_the_request(self):
        mock_client = Mock()
        mock_client.token.check.side_effect = requests.RequestException
        auth_verifier = StubVerifier()
        auth_verifier.set_client(mock_client)

        @auth_verifier.verify_token
        @required_acl('foo')
        def decorated():
            return s.result

        decorated()

        assert_that(self.request_mock.token_id, equal_to(s.token))

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

    def test_verify_invalid_token_calls_handle_invalid_token(self):
        mock_client = Mock()
        mock_client.token.check.side_effect = InvalidTokenException
        auth_verifier = StubVerifier()
        auth_verifier.set_client(mock_client)

        @auth_verifier.verify_token
        @required_acl('foo')
        def decorated():
            return s.result

        result = decorated()

        assert_that(result, equal_to(s.invalid_token))

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

    def test_verify_tenant_calls_handle_unauthorized_when_404(self):
        mock_client = Mock()
        response = Mock(status_code=404)
        exception = requests.RequestException(response=response)
        mock_client.token.get.side_effect = exception
        auth_verifier = StubVerifier()
        auth_verifier.set_client(mock_client)

        @auth_verifier.verify_tenant
        @required_tenant('foo')
        def decorated():
            return s.result

        result = decorated()

        assert_that(result, equal_to(s.unauthorized))

    def test_verify_token_raise_not_implemented_when_invalid_without_raising(self):
        mock_client = Mock()
        mock_client.token.check.return_value = False
        auth_verifier = StubVerifier()
        auth_verifier.set_client(mock_client)

        @auth_verifier.verify_token
        @required_acl('foo')
        def decorated():
            return s.result

        assert_that(
            calling(decorated),
            raises(NotImplementedError),
        )

    def test_token_empty(self):
        self.request_mock.headers = {}
        auth_verifier = AuthVerifier()

        token = auth_verifier.token()

        assert_that(token, equal_to(''))

    def test_token_not_empty(self):
        self.request_mock.headers = {'X-Auth-Token': s.token}
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

    def test_token_content_from_the_request(self):
        original_content = {'metadata': {'foo': 'bar'}}
        mock_client = Mock()
        mock_client.token.check.return_value = True
        mock_client.token.get.return_value = original_content
        auth_verifier = StubVerifier()
        auth_verifier.set_client(mock_client)

        @auth_verifier.verify_token
        @required_acl('foo')
        def decorated():
            return self.request_mock.token_content

        token_content = decorated()

        assert_that(token_content, equal_to(original_content))
        mock_client.token.get.assert_called_once_with(s.token)

        mock_client.reset_mock()

        # Second call should hit the cache
        token_content = decorated()

        assert_that(token_content, equal_to(mock_client.token.get.return_value))
        mock_client.token.get.assert_not_called()

    def test_user_uuid_to_the_request(self):
        self.request_mock._token_content = {'metadata': {'uuid': s.uuid}}
        mock_client = Mock()
        mock_client.token.check.return_value = True
        auth_verifier = StubVerifier()
        auth_verifier.set_client(mock_client)

        @auth_verifier.verify_token
        @required_acl('foo')
        def decorated():
            return self.request_mock.user_uuid

        user_uuid = decorated()

        assert_that(user_uuid, equal_to(s.uuid))


class TestAccessCheck:
    scenarios = [
        {
            'scenario': 'user_access_ends_with_hashtag',
            'acl': ['foo.bar.#'],
            'tests': [
                ('foo.bar', False),
                ('foo.bar.toto', True),
                ('foo.bar.toto.tata', True),
                ('other.bar.toto', False),
                ('foo.bar.*', True),
                ('foo.bar.*.*', True),
                ('foo.bar.#', True),
                ('*.bar.toto', False),
                ('*.*.toto', False),
                ('#.bar.toto', False),
            ],
        },
        {
            'scenario': 'user_access_has_not_special_character',
            'acl': ['foo.bar.toto'],
            'tests': [
                ('foo.bar.toto', True),
                ('foo.bar.toto.tata', False),
                ('other.bar.toto', False),
                ('foo.bar.*', False),
                ('foo.bar.#', False),
                ('*.bar.toto', False),
                ('#.bar.toto', False),
            ],
        },
        {
            'scenario': 'user_access_has_asterisks',
            'acl': ['foo.*.*'],
            'tests': [
                ('foo.bar.toto', True),
                ('foo.bar.toto.tata', False),
                ('other.bar.toto', False),
                ('foo.*.*', True),
                ('foo.*', False),
                ('foo.bar.#', False),
                ('*.bar.toto', False),
                ('#.bar.toto', False),
            ],
        },
        {
            'scenario': 'with_multiple_accesses',
            'acl': ['foo', 'foo.bar.toto', 'other.#'],
            'tests': [
                ('foo', True),
                ('foo.bar', False),
                ('foo.bar.toto', True),
                ('foo.bar.toto.tata', False),
                ('other.bar.toto', True),
                ('*', False),
                ('*.*.toto', False),
                ('#', False),
            ],
        },
        {
            'scenario': 'user_access_has_hashtag_in_middle',
            'acl': ['foo.bar.#.titi'],
            'tests': [
                ('foo.bar', False),
                ('foo.bar.toto', False),
                ('foo.bar.toto.tata', False),
                ('foo.bar.toto.tata.titi', True),
                ('foo.bar.#.titi', True),
                ('foo.bar.*.*', False),
                ('foo.bar.*.titi', True),
                ('foo.bar.*.*.titi', True),
                ('foo.bar.#', False),
            ],
        },
        {
            'scenario': 'user_access_ends_with_me',
            'acl': ['foo.#.me'],
            'tests': [
                ('foo.bar', False),
                ('foo.bar.me', True),
                ('foo.bar.123', True),
                ('foo.bar.toto.me', True),
                ('foo.bar.toto.123', True),
                ('foo.bar.toto.me.titi', False),
                ('foo.bar.toto.123.titi', False),
                ('foo.*.123', True),
                ('foo.*.456', False),
                ('foo.#.me', True),
                ('foo.#.notme', False),
                ('foo.*.*.123', True),
                ('foo.*', False),
                ('foo.#', False),
            ],
        },
        {
            'scenario': 'user_access_has_me_in_middle',
            'acl': ['foo.#.me.bar'],
            'tests': [
                ('foo.bar.123', False),
                ('foo.bar.me', False),
                ('foo.bar.123.bar', True),
                ('foo.bar.me.bar', True),
                ('foo.bar.toto.123.bar', True),
                ('foo.bar.toto.me.bar', True),
                ('foo.*.123.bar', True),
                ('foo.*.456.bar', False),
                ('foo.#.me.bar', True),
                ('foo.#.notme.bar', False),
                ('foo.*.*.123.bar', True),
                ('foo.*.bar', False),
                ('foo.#.bar', False),
            ],
        },
        {
            'scenario': 'negating',
            'acl': ['!foo.me.bar'],
            'tests': [
                ('foo.me.bar', False),
            ],
        },
        {
            'scenario': 'negating_multiple_identical_accesses',
            'acl': ['foo.me.bar', '!foo.me.bar', 'foo.me.bar'],
            'tests': [
                ('foo.me.bar', False),
            ],
        },
        {
            'scenario': 'negating_ending_hashtag',
            'acl': ['!foo.me.bar.#', 'foo.me.bar.123'],
            'tests': [
                ('foo.me.bar.123', False),
            ],
        },
        {
            'scenario': 'negating_hashtag_sublevel',
            'acl': ['foo.#', '!foo.me.bar.#', 'foo.me.bar.123'],
            'tests': [
                ('foo.me.bar.123', False),
            ],
        },
        {
            'scenario': 'negating_specific',
            'acl': ['foo.*.bar', '!foo.123.bar'],
            'tests': [
                ('foo.me.bar', True),
                ('foo.123.bar', False),
            ],
        },
        {
            'scenario': 'negating_toplevel',
            'acl': ['!*.bar', 'foo.bar'],
            'tests': [
                ('foo.bar', False),
            ],
        },
    ]
    parameters = [
        (scenario['acl'], access, result)
        for scenario in scenarios
        for (access, result) in scenario['tests']
    ]

    @pytest.mark.parametrize(['acl', 'access', 'expected_result'], parameters)
    def test_matches_required_access(self, acl, access, expected_result):
        check = AccessCheck('123', 'session-uuid', acl)
        assert_that(check.matches_required_access(access), is_(expected_result))

    def test_matches_required_access_with_negative_access(self):
        check = AccessCheck('123', 'session-uuid', ['foo.bar'])

        assert_that(check.matches_required_access('!foo.bar'), is_(False))
        assert_that(check.matches_required_access('!anything'), is_(False))

    @pytest.mark.parametrize(['acl', 'access', 'expected_result'], parameters)
    def test_may_add_access(self, acl, access, expected_result):
        check = AccessCheck('123', 'session-uuid', acl)
        assert_that(check.may_add_access(access), is_(expected_result))

    def test_may_add_access_with_negative_access(self):
        check = AccessCheck('123', 'session-uuid', ['foo.bar'])

        assert_that(check.may_add_access('!foo.bar'), is_(True))
        assert_that(check.may_add_access('!anything'), is_(True))

    def test_matches_my_session(self):
        check = AccessCheck('123', 'session-uuid', ['foo.my_session'])

        assert_that(check.matches_required_access('foo.session-uuid'))
        assert_that(check.matches_required_access('foo.my_session'))
        assert_that(
            check.matches_required_access('foo.another-session-uuid'),
            equal_to(False),
        )
