# -*- coding: utf-8 -*-
# Copyright 2018-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import requests
from hamcrest import (
    assert_that,
    calling,
    equal_to,
    instance_of,
)
from mock import Mock, patch
from xivo.auth_verifier import AuthServerUnreachable
from xivo_test_helpers.hamcrest.raises import raises
from unittest import TestCase

from ..tenant_helpers import (
    InvalidTenant,
    InvalidToken,
    Tenant,
    Tokens,
    UnauthorizedTenant,
    User,
    Users,
)


class TestTenantAutodetect(TestCase):

    @patch('xivo.tenant_helpers.request')
    def test_given_no_token_when_autodetect_then_raise(self, request):
        tokens = Mock()
        tokens.from_headers.side_effect = InvalidToken
        request.headers = {}

        assert_that(
            calling(Tenant.autodetect).with_args(tokens),
            raises(InvalidToken)
        )

    @patch('xivo.tenant_helpers.request')
    def test_given_token_no_tenant_when_autodetect_then_return_tenant_from_token(self, request):
        tenant = 'tenant'
        tokens = Mock()
        tokens.from_headers.return_value = Mock(tenant_uuid=tenant)
        request.headers = {'X-Auth-Token': 'token'}

        result = Tenant.autodetect(tokens)

        assert_that(result.uuid, equal_to(tenant))

    @patch('xivo.tenant_helpers.request')
    def test_given_token_and_tenant_when_autodetect_then_return_given_tenant(self, request):
        tenant = 'tenant'
        token = Mock(tenant_uuid=tenant)
        token.visible_tenants.return_value = [tenant]
        tokens = Mock()
        tokens.from_headers.return_value = token
        request.headers = {'X-Auth-Token': 'token', 'Wazo-Tenant': tenant}

        result = Tenant.autodetect(tokens)

        assert_that(result.uuid, equal_to(tenant))

    @patch('xivo.tenant_helpers.request')
    def test_given_token_unknown_tenant_and_user_in_tenant_when_autodetect_then_return_tenant(self, request):
        tenant = 'tenant'
        other = 'other'
        token = Mock(tenant_uuid=other)
        token.visible_tenants.return_value = [Mock(uuid=tenant), Mock(uuid=other)]
        tokens = Mock()
        tokens.from_headers.return_value = token
        request.headers = {
            'X-Auth-Token': 'token',
            'Wazo-Tenant': tenant,
        }

        result = Tenant.autodetect(tokens)

        assert_that(result.uuid, equal_to(tenant))

    @patch('xivo.tenant_helpers.request')
    def test_given_token_unknown_tenant_and_user_not_in_tenant_when_autodetect_then_raise(self, request):
        tenant = 'tenant'
        other = 'other'
        token = Mock(tenant_uuid=other)
        token.visible_tenants.return_value = []
        tokens = Mock()
        tokens.from_headers.return_value = token
        request.headers = {
            'X-Auth-Token': 'token',
            'Wazo-Tenant': tenant,
        }

        assert_that(
            calling(Tenant.autodetect).with_args(tokens),
            raises(UnauthorizedTenant)
        )


class TestTenantFromHeaders(TestCase):

    @patch('xivo.tenant_helpers.request')
    def test_given_no_tenant_when_from_headers_then_raise(self, request):
        request.headers = {}

        assert_that(
            calling(Tenant.from_headers),
            raises(InvalidTenant)
        )

    @patch('xivo.tenant_helpers.request')
    def test_given_tenant_when_from_headers_then_return_tenant(self, request):
        tenant = 'tenant'
        request.headers = {'Wazo-Tenant': tenant}

        result = Tenant.from_headers()

        assert_that(result.uuid, equal_to(tenant))

    @patch('xivo.tenant_helpers.request')
    def test_given_multiple_tenant_when_from_headers_then_raise(self, request):
        tenant = 'tenant1,tenant2'
        request.headers = {'Wazo-Tenant': tenant}

        assert_that(
            calling(Tenant.from_headers),
            raises(InvalidTenant)
        )


class TestTenantFromToken(TestCase):

    def test_given_no_tenant_when_from_token_then_return_tenant(self):
        token = Mock(tenant_uuid=None)

        assert_that(
            calling(Tenant.from_token).with_args(token),
            raises(InvalidTenant)
        )

    def test_given_tenant_when_from_token_then_return_tenant(self):
        tenant = 'tenant'
        token = Mock(tenant_uuid=tenant)

        result = Tenant.from_token(token)

        assert_that(result.uuid, equal_to(tenant))


class TestTenantCheckAgainstToken(TestCase):

    def test_when_token_has_no_tenant_uuid_and_no_visible_tenants(self):
        tenant_uuid = 'tenant'
        tenant = Tenant(tenant_uuid)
        token = Mock(tenant_uuid=None)
        token.visible_tenants.return_value = []

        assert_that(
            calling(tenant.check_against_token).with_args(token),
            raises(InvalidTenant)
        )

    def test_when_token_has_same_tenant_uuid(self):
        tenant_uuid = 'tenant'
        tenant = Tenant(tenant_uuid)
        token = Mock(tenant_uuid=tenant_uuid)
        token.visible_tenants.return_value = []

        result = tenant.check_against_token(token)

        assert_that(result.uuid, equal_to(tenant_uuid))

    def test_when_tenant_in_visible_tenants(self):
        tenant = Tenant('subtenant')
        token = Mock(tenant_uuid='supertenant')
        token.visible_tenants.return_value = [Tenant('subtenant'), Tenant('othertenant')]

        result = tenant.check_against_token(token)

        assert_that(result.uuid, equal_to('subtenant'))

    def test_when_tenant_not_in_visible_tenants(self):
        tenant = Tenant('othertenant')
        token = Mock(tenant_uuid='supertenant')
        token.visible_tenants.return_value = [Tenant('subtenant')]

        assert_that(
            calling(tenant.check_against_token).with_args(token),
            raises(InvalidTenant)
        )


class TestTokensGet(TestCase):

    def test_given_no_auth_server_when_get_then_raise(self):
        auth = Mock()
        auth.token.get.side_effect = requests.RequestException
        tokens = Tokens(auth)

        assert_that(
            calling(tokens.get).with_args('token'),
            raises(AuthServerUnreachable)
        )

    def test_given_unknown_token_when_get_then_raise(self):
        auth = Mock()
        auth.token.get.side_effect = requests.HTTPError
        tokens = Tokens(auth)

        assert_that(
            calling(tokens.get).with_args('token'),
            raises(InvalidToken)
        )

    def test_given_correct_token_id_when_get_then_return_token(self):
        auth = Mock()
        auth.token.get.return_value = {'token': 'token'}
        tokens = Tokens(auth)

        result = tokens.get('token')

        assert_that(result.uuid, equal_to('token'))


class TestTokensFromHeaders(TestCase):

    @patch('xivo.tenant_helpers.extract_token_id_from_header')
    def test_given_no_header_when_get_then_raise(self, extract):
        extract.return_value = ''
        auth = Mock()
        tokens = Tokens(auth)

        assert_that(
            calling(tokens.from_headers),
            raises(InvalidToken)
        )

    @patch('xivo.tenant_helpers.extract_token_id_from_header')
    def test_given_header_token_when_get_then_return_token(self, extract):
        extract.return_value = token_id = 'token'
        auth = Mock()
        auth.token.get.return_value = {'token': token_id}
        tokens = Tokens(auth)

        result = tokens.get(token_id)

        assert_that(result.uuid, equal_to(token_id))


class TestUsersGet(TestCase):

    def test_when_get_then_return_user(self):
        auth = Mock()
        users = Users(auth)

        result = users.get('user-uuid')

        assert_that(result, instance_of(User))
