# -*- coding: utf-8 -*-
# Copyright 2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import requests
from hamcrest import (
    assert_that,
    equal_to,
    calling,
    raises
)
from mock import Mock, patch
from xivo.auth_verifier import AuthServerUnreachable
from unittest import TestCase

from ..tenant_helpers import (
    CachedTokens,
    InvalidTenant,
    InvalidToken,
    Tenant,
    Tokens,
    UnauthorizedTenant
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
    def test_given_token_no_tenant_when_autodetect_then_return_tenant(self, request):
        tenant = 'tenant'
        tokens = Mock()
        tokens.from_headers.return_value = {'metadata': {'tenants': [{'uuid': tenant}]}}
        request.headers = {'X-Auth-Token': 'token'}

        result = Tenant.autodetect(tokens)

        assert_that(result.uuid, equal_to(tenant))

    @patch('xivo.tenant_helpers.request')
    def test_given_token_and_unknown_tenant_when_autodetect_then_raise(self, request):
        tenant = 'tenant'
        tokens = Mock()
        tokens.from_headers.return_value = {'metadata': {'tenants': [{'uuid': tenant}]}}
        request.headers = {'X-Auth-Token': 'token',
                           'Wazo-Tenant': 'unknown-tenant'}

        assert_that(
            calling(Tenant.autodetect).with_args(tokens),
            raises(UnauthorizedTenant)
        )

    @patch('xivo.tenant_helpers.request')
    def test_given_token_and_tenant_when_autodetect_then_return_tenant(self, request):
        tenant = 'tenant'
        tokens = Mock()
        tokens.from_headers.return_value = {'metadata': {'tenants': [{'uuid': tenant}]}}
        request.headers = {'X-Auth-Token': 'token',
                           'Wazo-Tenant': tenant}

        result = Tenant.autodetect(tokens)

        assert_that(result.uuid, equal_to(tenant))


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


class TestTenantCheckAgainst(TestCase):

    def test_given_no_token_metadata_when_check_against_then_raise(self):
        tenant_uuid = 'tenant'
        token = {'metadata': {}}

        tenant = Tenant(tenant_uuid)

        assert_that(
            calling(tenant.check_against).with_args(token),
            raises(InvalidTenant)
        )

    def test_given_token_has_tenant_when_check_against_then_return_tenant(self):
        tenant_uuid = 'tenant'
        token = {'metadata': {'tenants': [{'uuid': tenant_uuid}]}}
        tenant = Tenant(tenant_uuid)

        result = tenant.check_against(token)

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
