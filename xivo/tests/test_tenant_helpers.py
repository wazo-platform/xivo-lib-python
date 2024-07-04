# Copyright 2018-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from unittest import TestCase
from unittest.mock import Mock, patch

from hamcrest import (
    assert_that,
    calling,
    contains_exactly,
    empty,
    equal_to,
    has_property,
)
from requests import HTTPError, RequestException
from wazo_test_helpers.hamcrest.raises import raises

from xivo.auth_verifier import AuthServerUnreachable

from ..tenant_helpers import (
    InvalidTenant,
    InvalidToken,
    Tenant,
    Token,
    UnauthorizedTenant,
)


class TestTenantAutodetect(TestCase):
    @patch('xivo.tenant_helpers.Token')
    @patch('xivo.tenant_helpers.request', spec={})
    def test_given_no_token_when_autodetect_then_raise(self, request, Token):
        auth = Mock()
        Token.from_headers = Mock()
        Token.from_headers.side_effect = InvalidToken()

        request.headers = {}

        assert_that(calling(Tenant.autodetect).with_args(auth), raises(InvalidToken))

    @patch('xivo.tenant_helpers.Token')
    @patch('xivo.tenant_helpers.request', spec={})
    def test_given_token_no_tenant_when_autodetect_then_return_tenant_from_token(
        self, request, Token
    ):
        tenant = 'tenant'
        token = Mock(tenant_uuid=tenant)
        auth = Mock()
        Token.from_headers = Mock()
        Token.from_headers.return_value = token
        request.headers = {'X-Auth-Token': 'token'}

        result = Tenant.autodetect(auth)

        assert_that(result.uuid, equal_to(tenant))

    @patch('xivo.tenant_helpers.Token')
    @patch('xivo.tenant_helpers.request', spec={})
    def test_given_token_and_tenant_when_autodetect_then_return_given_tenant(
        self, request, Token
    ):
        tenant = 'tenant'
        token = Mock(tenant_uuid=tenant)
        auth = Mock()
        Token.from_headers = Mock()
        Token.from_headers.return_value = token
        request.headers = {'X-Auth-Token': 'token', 'Wazo-Tenant': tenant}

        result = Tenant.autodetect(auth)

        assert_that(result.uuid, equal_to(tenant))

    @patch('xivo.tenant_helpers.Token')
    @patch('xivo.tenant_helpers.request', spec={})
    def test_given_token_unknown_tenant_and_user_in_tenant_when_autodetect_then_return_tenant(
        self, request, Token
    ):
        tenant = 'tenant'
        other = 'other'
        token = Mock(tenant_uuid=other)
        token.is_tenant_allowed.return_value = True
        auth = Mock()
        Token.from_headers = Mock()
        Token.from_headers.return_value = token
        request.headers = {'X-Auth-Token': 'token', 'Wazo-Tenant': tenant}

        result = Tenant.autodetect(auth)

        assert_that(result.uuid, equal_to(tenant))

    @patch('xivo.tenant_helpers.Token')
    @patch('xivo.tenant_helpers.request', spec={})
    def test_given_token_unknown_tenant_and_user_not_in_tenant_when_autodetect_then_raise(
        self, request, Token
    ):
        tenant = 'tenant'
        other = 'other'
        token = Mock(tenant_uuid=other)
        token.is_tenant_allowed.return_value = False
        auth = Mock()
        Token.from_headers = Mock()
        Token.from_headers.return_value = token
        request.headers = {'X-Auth-Token': 'token', 'Wazo-Tenant': tenant}

        assert_that(
            calling(Tenant.autodetect).with_args(auth), raises(UnauthorizedTenant)
        )

    def test_given_visible_tenants_called_twice_with_same_tenant(self):
        base_tenant = 'base-tenant-uuid'
        tenant = Tenant('tenant-uuid')
        token = Token(Mock(), Mock())
        token._cache_tenants = {base_tenant: [tenant]}

        assert_that(token.visible_tenants(base_tenant), equal_to([tenant]))


class TestTenantFromHeaders(TestCase):
    @patch('xivo.tenant_helpers.request', spec={})
    def test_given_no_tenant_when_from_headers_then_raise(self, request):
        request.headers = {}

        assert_that(calling(Tenant.from_headers), raises(InvalidTenant))

    @patch('xivo.tenant_helpers.request', spec={})
    def test_given_tenant_when_from_headers_then_return_tenant(self, request):
        tenant = 'tenant'
        request.headers = {'Wazo-Tenant': tenant}

        result = Tenant.from_headers()

        assert_that(result.uuid, equal_to(tenant))


class TestTenantFromQuery(TestCase):
    @patch('xivo.tenant_helpers.request', spec={})
    def test_given_no_tenant_when_from_query_then_raise(self, mock_request):
        mock_request.args = {}

        assert_that(calling(Tenant.from_query), raises(InvalidTenant))

    @patch('xivo.tenant_helpers.request', spec={})
    def test_given_tenant_when_from_query_then_return_tenant(self, mock_request):
        tenant = 'tenant'
        mock_request.args = {'tenant': tenant}

        result = Tenant.from_query()

        assert_that(result.uuid, equal_to(tenant))


class TestTenantFromToken(TestCase):
    def test_given_no_tenant_when_from_token_then_return_tenant(self):
        token = Mock(tenant_uuid=None)

        assert_that(calling(Tenant.from_token).with_args(token), raises(InvalidTenant))

    def test_given_tenant_when_from_token_then_return_tenant(self):
        tenant = 'tenant'
        token = Mock(tenant_uuid=tenant)

        result = Tenant.from_token(token)

        assert_that(result.uuid, equal_to(tenant))


class TestTenantCheckAgainstToken(TestCase):
    def test_when_token_has_no_tenant_uuid_and_has_no_tenant_access(self):
        tenant_uuid = 'tenant'
        tenant = Tenant(tenant_uuid)
        token = Mock(tenant_uuid=None)
        token.is_tenant_allowed.return_value = False

        assert_that(
            calling(tenant.check_against_token).with_args(token), raises(InvalidTenant)
        )

    def test_when_is_tenant_allowed(self):
        tenant = Tenant('subtenant')
        token = Mock(tenant_uuid='supertenant')
        token.is_tenant_allowed.return_value = True

        result = tenant.check_against_token(token)

        assert_that(result.uuid, equal_to('subtenant'))

    def test_when_is_tenant_allowed_return_error(self):
        tenant = Tenant('othertenant')
        token = Mock(tenant_uuid='supertenant')
        token.is_tenant_allowed.side_effect = InvalidTenant()

        assert_that(
            calling(tenant.check_against_token).with_args(token), raises(InvalidTenant)
        )

    def test_when_has_no_tenant_access(self):
        tenant = Tenant('othertenant')
        token = Mock(tenant_uuid='supertenant')
        token.is_tenant_allowed.return_value = False

        assert_that(
            calling(tenant.check_against_token).with_args(token), raises(InvalidTenant)
        )


class TestTokenFromHeaders(TestCase):
    @patch('xivo.tenant_helpers.extract_token_id_from_header')
    def test_given_valid_header(self, extract):
        token_id = 'my-valid-uuid'
        extract.return_value = token_id
        auth = Mock()

        token = Token.from_headers(auth)

        assert_that(token.uuid, equal_to(token_id))

    @patch('xivo.tenant_helpers.extract_token_id_from_header')
    def test_given_no_header_when_get_then_raise(self, extract):
        extract.return_value = ''
        auth = Mock()

        assert_that(calling(Token.from_headers).with_args(auth), raises(InvalidToken))


class TestTokenVisibleTenants(TestCase):
    def test_without_tenant_uuid(self):
        auth = Mock()
        token_uuid = 'my-token-uuid'
        token_dict = {'token': token_uuid, 'metadata': {}}
        auth.token.get.return_value = token_dict
        token = Token(token_uuid, auth)

        result = token.visible_tenants()

        assert_that(result, empty())

    def test_auth_unauthorized(self):
        auth = Mock()
        token_uuid = 'my-token-uuid'
        token_dict = {'token': token_uuid, 'metadata': {'tenant_uuid': 'tenant'}}
        auth.token.get.return_value = token_dict
        token = Token(token_uuid, auth)
        auth.tenants.list.side_effect = HTTPError(response=Mock(status_code=401))

        result = token.visible_tenants()

        assert_that(result, contains_exactly(has_property('uuid', 'tenant')))

    def test_auth_exception(self):
        auth = Mock()
        token = Token('token', auth)
        auth.tenants.list.side_effect = RequestException()

        assert_that(
            calling(token.visible_tenants).with_args('tenant'),
            raises(AuthServerUnreachable),
        )

    def test_visible_tenants(self):
        auth = Mock()
        token_uuid = 'my-token-uuid'
        token_dict = {'token': token_uuid, 'metadata': {'tenant_uuid': 'supertenant'}}
        auth.token.get.return_value = token_dict
        token = Token(token_uuid, auth)
        auth.tenants.list.return_value = {
            'items': [
                {'name': 'supertenant-name', 'uuid': 'supertenant'},
                {'name': 'subtenant1-name', 'uuid': 'subtenant1'},
                {'name': 'subtenant2-name', 'uuid': 'subtenant2'},
            ]
        }

        result = token.visible_tenants()

        assert_that(
            result,
            contains_exactly(
                has_property('uuid', 'supertenant'),
                has_property('uuid', 'subtenant1'),
                has_property('uuid', 'subtenant2'),
            ),
        )

    def test_visible_tenants_with_specified_tenant_uuid(self):
        auth = Mock()
        token = Token('token', auth)
        auth.tenants.list.return_value = {
            'items': [
                {'name': 'supertenant-name', 'uuid': 'supertenant'},
                {'name': 'subtenant1-name', 'uuid': 'subtenant1'},
                {'name': 'subtenant2-name', 'uuid': 'subtenant2'},
            ]
        }

        result = token.visible_tenants("supertenant")

        assert_that(
            result,
            contains_exactly(
                has_property('uuid', 'supertenant'),
                has_property('uuid', 'subtenant1'),
                has_property('uuid', 'subtenant2'),
            ),
        )

    def test_auth_unauthorized_with_specified_tenant(self):
        auth = Mock()
        token_uuid = 'my-token-uuid'
        token_dict = {'token': token_uuid, 'metadata': {'tenant_uuid': 'tenant'}}
        auth.token.get.return_value = token_dict
        token = Token(token_uuid, auth)
        auth.tenants.list.side_effect = HTTPError(response=Mock(status_code=401))

        result = token.visible_tenants("tenant")
        assert_that(result, contains_exactly(has_property('uuid', 'tenant')))

        assert_that(
            calling(token.visible_tenants).with_args("other"),
            raises(InvalidTenant),
        )


class TestTokenIsTenantAllowed(TestCase):
    def test_auth_exception(self):
        auth = Mock()
        token = Token('token', auth)
        auth.token.is_valid.side_effect = RequestException()

        assert_that(
            calling(token.is_tenant_allowed).with_args('tenant_uuid'),
            raises(AuthServerUnreachable),
        )

    def test_has_not_access(self):
        auth = Mock()
        token = Token('token', auth)
        auth.token.is_valid.return_value = False

        has_access = token.is_tenant_allowed('tenant_uuid')

        assert_that(not has_access)

    def test_has_access(self):
        auth = Mock()
        token = Token('token', auth)
        auth.token.is_valid.return_value = True

        has_access = token.is_tenant_allowed('tenant_uuid')

        assert_that(has_access)

    def test_tenant_is_none(self):
        auth = Mock()
        token = Token('token', auth)

        has_access = token.is_tenant_allowed(None)

        assert_that(not has_access)

    def test_tenant_is_same_as_token_when_already_fetched(self):
        auth = Mock()
        token = Token('token', auth)
        auth.token.get.return_value = {'metadata': {'tenant_uuid': 'tenant_uuid'}}
        token.tenant_uuid  # fetch token

        has_access = token.is_tenant_allowed('tenant_uuid')

        auth.token.is_valid.assert_not_called()
        assert_that(has_access)

    def test_tenant_is_different_as_token_when_already_fetched(self):
        auth = Mock()
        token = Token('token', auth)
        auth.token.get.return_value = {'metadata': {'tenant_uuid': 'tenant_uuid'}}
        token.tenant_uuid  # fetch token

        token.is_tenant_allowed('other_uuid')

        auth.token.is_valid.assert_called_once_with('token', tenant='other_uuid')


class TestTokenProperties(TestCase):
    def test_token_dict_cached(self):
        auth = Mock()
        token_uuid = 'my-token-uuid'
        token_dict = {'token': token_uuid, 'metadata': {}}
        auth.token.get.return_value = token_dict
        token = Token(token_uuid, auth)

        result = token._token_dict

        auth.token.get.assert_called_once_with(token_uuid)
        assert_that(result, equal_to(token_dict))

        auth.token.get.reset_mock()
        result = token._token_dict

        auth.token.get.assert_not_called()
        assert_that(token.infos, equal_to(token_dict))

    def test_infos(self):
        auth = Mock()
        token_uuid = 'my-token-uuid'
        token_dict = {'token': token_uuid, 'metadata': {}}
        auth.token.get.return_value = token_dict
        token = Token(token_uuid, auth)

        result = token.infos

        assert_that(result, equal_to(token_dict))

    def test_tenant_uuid(self):
        auth = Mock()
        token_uuid = 'my-token-uuid'
        tenant_uuid = 'my-tenant-uuid'
        token_dict = {'token': token_uuid, 'metadata': {'tenant_uuid': tenant_uuid}}
        auth.token.get.return_value = token_dict
        token = Token(token_uuid, auth)

        result = token.tenant_uuid

        assert_that(result, equal_to(tenant_uuid))

    def test_user_uuid(self):
        auth = Mock()
        token_uuid = 'my-token-uuid'
        user_uuid = 'my-user-uuid'
        token_dict = {'token': token_uuid, 'metadata': {'uuid': user_uuid}}
        auth.token.get.return_value = token_dict
        token = Token(token_uuid, auth)

        result = token.user_uuid

        assert_that(result, equal_to(user_uuid))
