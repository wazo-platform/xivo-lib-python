# Copyright 2015-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from unittest.mock import Mock, PropertyMock, patch
from unittest.mock import sentinel as s

import pytest
import requests
from hamcrest import assert_that, equal_to, is_
from wazo_auth_client.exceptions import (
    InvalidTokenException,
    MissingPermissionsTokenException,
)

from ..auth_verifier import (
    AccessCheck,
    AuthServerUnreachable,
    AuthVerifier,
    AuthVerifierHelpers,
    Unauthorized,
    no_auth,
    required_acl,
    required_tenant,
)
from ..http_exceptions import (
    InvalidTokenAPIException,
    MissingPermissionsTokenAPIException,
)


class TestAuthVerifier(unittest.TestCase):
    def test_verify_tenant_raise_unauthorized(self):
        mock_client = Mock()
        auth_verifier = AuthVerifier()
        mock_token = Mock(uuid=s.token)
        type(mock_token).tenant_uuid = PropertyMock(
            side_effect=InvalidTokenAPIException(s.token)
        )
        mock_g = Mock()
        g_data = {
            'auth_client': mock_client,
            'token': mock_token,
            'token_extractor': None,
        }
        mock_g.get.side_effect = lambda x: g_data[x]

        @auth_verifier.verify_tenant
        @required_acl('foo')
        def decorated():
            return s.result

        with patch('xivo.auth_verifier.g', mock_g):
            with patch('xivo.tenant_flask_helpers.g', mock_g):
                with pytest.raises(Unauthorized) as exc_info:
                    decorated()
        assert exc_info.value.details['invalid_token'] == s.token

    def test_verify_tenant_raise_unreacheable(self):
        mock_client = Mock(host=s.host, port=s.port)
        auth_verifier = AuthVerifier()
        mock_token = Mock()
        type(mock_token).uuid = PropertyMock(
            side_effect=AuthServerUnreachable(s.host, s.port, s.error)
        )
        mock_g = Mock()
        g_data = {
            'auth_client': mock_client,
            'token': mock_token,
            'token_extractor': None,
        }
        mock_g.get.side_effect = lambda x: g_data[x]

        @auth_verifier.verify_tenant
        @required_acl('foo')
        def decorated():
            return s.result

        with patch('xivo.auth_verifier.g', mock_g):
            with patch('xivo.tenant_flask_helpers.g', mock_g):
                with pytest.raises(AuthServerUnreachable) as exc_info:
                    decorated()

        assert exc_info.value.details['auth_server_host'] == s.host
        assert exc_info.value.details['auth_server_port'] == s.port
        assert exc_info.value.details['original_error'] == str(s.error)


class TestAuthVerifierHelpers(unittest.TestCase):
    def test_validate_token_calls_auth_client(self):
        mock_client = Mock()
        token_uuid = s.token
        tenant_uuid = s.tenant
        helpers = AuthVerifierHelpers()

        @required_acl('foo')
        def endpoint():
            pass

        helpers.validate_token(endpoint, mock_client, token_uuid, tenant_uuid, {})

        mock_client.token.check.assert_called_once_with(s.token, 'foo', tenant=s.tenant)

    def test_validate_token_calls_function_when_no_auth(self):
        mock_client = Mock()
        mock_client.token.check.side_effect = MissingPermissionsTokenException
        token_uuid = s.token
        tenant_uuid = s.tenant
        helpers = AuthVerifierHelpers()

        @no_auth
        def endpoint():
            pass

        helpers.validate_token(endpoint, mock_client, token_uuid, tenant_uuid, {})

    def test_validate_token_with_no_acl_permission_raises_exception(self):
        mock_client = Mock()
        mock_client.token.check.side_effect = MissingPermissionsTokenException
        token_uuid = s.token
        tenant_uuid = s.tenant
        helpers = AuthVerifierHelpers()

        @required_acl('confd')
        def endpoint():
            pass

        with pytest.raises(MissingPermissionsTokenAPIException):
            helpers.validate_token(endpoint, mock_client, token_uuid, tenant_uuid, {})

    def test_validate_token_calls_function_when_valid(self):
        mock_client = Mock()
        mock_client.token.check.return_value = True
        token_uuid = s.token
        tenant_uuid = s.tenant
        helpers = AuthVerifierHelpers()

        @required_acl('foo')
        def endpoint():
            pass

        helpers.validate_token(endpoint, mock_client, token_uuid, tenant_uuid, {})

    def test_validate_tenant_calls_function_when_valid(self):
        tenant_uuid = s.tenant
        token_uuid = s.token
        helpers = AuthVerifierHelpers()

        @required_tenant(tenant_uuid)
        def endpoint():
            pass

        helpers.validate_tenant(endpoint, tenant_uuid, token_uuid)

    def test_validate_token_raise_unreachable(self):
        mock_client = Mock()
        mock_client.token.check.side_effect = requests.RequestException
        token_uuid = s.token
        tenant_uuid = s.tenant
        helpers = AuthVerifierHelpers()

        @required_acl('foo')
        def endpoint():
            pass

        with pytest.raises(AuthServerUnreachable):
            helpers.validate_token(endpoint, mock_client, token_uuid, tenant_uuid, {})

    def test_validate_invalid_token_raise_invalid_token(self):
        mock_client = Mock()
        mock_client.token.check.side_effect = InvalidTokenException
        token_uuid = s.token
        tenant_uuid = s.tenant
        helpers = AuthVerifierHelpers()

        @required_acl('foo')
        def endpoint():
            pass

        with pytest.raises(InvalidTokenAPIException):
            helpers.validate_token(endpoint, mock_client, token_uuid, tenant_uuid, {})

    def test_validate_tenant_raise_unauthorized(self):
        tenant_uuid = s.tenant
        token_uuid = s.token
        tenant_uuid = s.tenant
        different_tenant_uuid = s.different_tenant
        helpers = AuthVerifierHelpers()

        @required_tenant(different_tenant_uuid)
        def endpoint():
            pass

        with pytest.raises(Unauthorized):
            helpers.validate_tenant(endpoint, tenant_uuid, token_uuid)

    def test_validate_token_raise_not_implemented_when_invalid_without_raising(self):
        mock_client = Mock()
        mock_client.token.check.return_value = False
        token_uuid = s.token
        tenant_uuid = s.tenant
        helpers = AuthVerifierHelpers()

        @required_acl('foo')
        def endpoint():
            pass

        with pytest.raises(NotImplementedError):
            helpers.validate_token(endpoint, mock_client, token_uuid, tenant_uuid, {})


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
