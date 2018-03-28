# -*- coding: utf-8 -*-
# Copyright 2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import requests
from hamcrest import (
    assert_that,
    calling,
    contains,
    equal_to,
    empty,
    has_properties,
    instance_of,
)
from mock import Mock, patch
from xivo.auth_verifier import AuthServerUnreachable
from xivo_test_helpers.hamcrest.raises import raises
from unittest import TestCase

from ..tenant_helpers import (
    InvalidTenant,
    InvalidToken,
    InvalidUser,
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
        users = Mock()
        request.headers = {}

        assert_that(
            calling(Tenant.autodetect).with_args(tokens, users),
            raises(InvalidToken)
        )

    @patch('xivo.tenant_helpers.request')
    def test_given_token_no_tenant_when_autodetect_then_return_tenant(self, request):
        tenant = 'tenant'
        tokens = Mock()
        tokens.from_headers.return_value = {'metadata': {'tenants': [{'uuid': tenant}]}}
        users = Mock()
        request.headers = {'X-Auth-Token': 'token'}

        result = Tenant.autodetect(tokens, users)

        assert_that(result.uuid, equal_to(tenant))

    @patch('xivo.tenant_helpers.request')
    def test_given_token_and_tenant_when_autodetect_then_return_tenant(self, request):
        tenant = 'tenant'
        tokens = Mock()
        tokens.from_headers.return_value = {'metadata': {'tenants': [{'uuid': tenant}]}}
        users = Mock()
        request.headers = {'X-Auth-Token': 'token',
                           'Wazo-Tenant': tenant}

        result = Tenant.autodetect(tokens, users)

        assert_that(result.uuid, equal_to(tenant))

    @patch('xivo.tenant_helpers.request')
    def test_given_token_unknown_tenant_and_user_in_tenant_when_autodetect_then_return_tenant(self, request):
        tenant = 'tenant'
        tokens = Mock()
        tokens.from_headers.return_value = {'metadata': {'uuid': 'user', 'tenants': []}}
        users = Mock()
        users.get.return_value.tenants.return_value = [Mock(uuid=tenant)]
        request.headers = {'X-Auth-Token': 'token',
                           'Wazo-Tenant': tenant}

        result = Tenant.autodetect(tokens, users)

        assert_that(result.uuid, equal_to(tenant))

    @patch('xivo.tenant_helpers.request')
    def test_given_token_unknown_tenant_and_user_not_in_tenant_when_autodetect_then_raise(self, request):
        tenant = 'tenant'
        tokens = Mock()
        tokens.from_headers.return_value = {'metadata': {'uuid': 'user', 'tenants': []}}
        users = Mock()
        users.get.return_value.tenants.return_value = []
        request.headers = {'X-Auth-Token': 'token',
                           'Wazo-Tenant': tenant}

        assert_that(
            calling(Tenant.autodetect).with_args(tokens, users),
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

        assert_that(calling(Tenant.from_headers),
                    raises(InvalidTenant))


class TestTenantFromHeadersMany(TestCase):

    @patch('xivo.tenant_helpers.request')
    def test_given_no_tenant_when_from_headers_then_empty_list(self, request):
        request.headers = {}

        result = Tenant.from_headers(many=True)

        assert_that(result, empty())

    @patch('xivo.tenant_helpers.request')
    def test_given_tenant_when_from_headers_then_return_tenants(self, request):
        request.headers = {'Wazo-Tenant': 'tenant1, tenant2'}

        result = Tenant.from_headers(many=True)

        assert_that(result, contains(has_properties(uuid='tenant1'), has_properties(uuid='tenant2')))


class TestTenantFromToken(TestCase):

    def test_given_no_metadata_when_from_token_then_return_tenant(self):
        token = {'metadata': {}}

        assert_that(
            calling(Tenant.from_token).with_args(token),
            raises(InvalidTenant)
        )

    def test_given_no_tenant_when_from_token_then_return_tenant(self):
        token = {'metadata': {'tenants': []}}

        assert_that(
            calling(Tenant.from_token).with_args(token),
            raises(InvalidTenant)
        )

    def test_given_too_many_tenants_when_from_token_then_return_tenant(self):
        token = {'metadata': {'tenants': [{'uuid': 'tenant1'},
                                          {'uuid': 'tenant2'}]}}

        assert_that(
            calling(Tenant.from_token).with_args(token),
            raises(InvalidTenant)
        )

    def test_given_tenant_when_from_token_then_return_tenant(self):
        tenant = 'tenant'
        token = {'metadata': {'tenants': [{'uuid': tenant}]}}

        result = Tenant.from_token(token)

        assert_that(result.uuid, equal_to(tenant))


class TestTenantCheckAgainstToken(TestCase):

    def test_given_no_token_metadata_when_check_against_token_then_raise(self):
        tenant_uuid = 'tenant'
        token = {'metadata': {}}

        tenant = Tenant(tenant_uuid)

        assert_that(
            calling(tenant.check_against_token).with_args(token),
            raises(InvalidTenant)
        )

    def test_given_token_has_tenant_when_check_against_token_then_return_tenant(self):
        tenant_uuid = 'tenant'
        token = {'metadata': {'tenants': [{'uuid': tenant_uuid}]}}
        tenant = Tenant(tenant_uuid)

        result = tenant.check_against_token(token)

        assert_that(result.uuid, equal_to(tenant_uuid))


class TestTenantCheckAgainstUser(TestCase):

    def test_given_no_tenants_when_check_against_user_then_raise(self):
        tenant_uuid = 'tenant'
        user = Mock()
        user.tenants.return_value = []

        tenant = Tenant(tenant_uuid)

        assert_that(
            calling(tenant.check_against_user).with_args(user),
            raises(InvalidTenant)
        )

    def test_given_user_has_tenant_when_check_against_user_then_return_tenant(self):
        tenant_uuid = 'tenant'
        tenant = Tenant(tenant_uuid)
        user = Mock()
        user.tenants.return_value = [Tenant(tenant_uuid)]

        result = tenant.check_against_user(user)

        assert_that(result.uuid, equal_to(tenant_uuid))


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
        token = {'token': 'token'}
        auth = Mock()
        auth.token.get.return_value = token
        tokens = Tokens(auth)

        result = tokens.get('token')

        assert_that(result, equal_to(token))


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
        token = {'token': token_id}
        auth = Mock()
        auth.token.get.return_value = token
        tokens = Tokens(auth)

        result = tokens.get(token_id)

        assert_that(result, equal_to(token))


class TestUsersGet(TestCase):

    def test_when_get_then_return_user(self):
        auth = Mock()
        users = Users(auth)

        result = users.get('user-uuid')

        assert_that(result, instance_of(User))


class TestUserTenants(TestCase):

    def test_given_no_auth_server_when_tenants_then_raise(self):
        auth = Mock()
        auth.users.get_tenants.side_effect = requests.RequestException
        user = User(auth, 'user-uuid')

        assert_that(
            calling(user.tenants),
            raises(AuthServerUnreachable)
        )

    def test_given_unknown_user_when_tenants_then_raise(self):
        auth = Mock()
        auth.users.get_tenants.side_effect = requests.HTTPError
        user = User(auth, 'user-uuid')

        assert_that(
            calling(user.tenants),
            raises(InvalidUser)
        )

    def test_given_correct_user_id_when_tenants_then_return_tenants(self):
        user = {'uuid': 'user-uuid'}
        auth = Mock()
        auth.users.get_tenants.return_value = {'items': [{'uuid': 'tenant-uuid'}]}
        user = User(auth, 'user-uuid')

        result = user.tenants()

        assert_that(result, contains(has_properties(uuid='tenant-uuid')))

    def test_when_calling_tenants_multiple_time_then_dont_call_wazo_auth_again(self):
        user = {'uuid': 'user-uuid'}
        auth = Mock()
        exception = Exception('Should not be called again')
        auth.users.get_tenants.side_effect = [{'items': [{'uuid': 'tenant-uuid'}]}, exception]
        user = User(auth, 'user-uuid')

        result = user.tenants()
        result = user.tenants()

        assert_that(result, contains(has_properties(uuid='tenant-uuid')))
