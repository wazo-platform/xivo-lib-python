# -*- coding: utf-8 -*-
# Copyright 2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import requests
import flask

from flask import request
from xivo import rest_api_helpers
from xivo.auth_verifier import extract_token_id_from_header
from xivo.auth_verifier import AuthServerUnreachable


class InvalidTenant(Exception):
    def __init__(self, tenant_uuid=None):
        if tenant_uuid:
            super(InvalidTenant, self).__init__('Invalid tenant "{uuid}"'.format(uuid=tenant_uuid))
        else:
            super(InvalidTenant, self).__init__('Invalid tenant')


class InvalidToken(Exception):
    def __init__(self, token_id=None):
        if token_id:
            super(InvalidToken, self).__init__('Invalid token "{id}"'.format(id=token_id))
        else:
            super(InvalidToken, self).__init__('Invalid token')


class UnauthorizedTenant(rest_api_helpers.APIException):

    def __init__(self, tenant):
        super(UnauthorizedTenant, self).__init__(
            status_code=401,
            message='Unauthorized tenant',
            error_id='unauthorized-tenant',
            details={
                'tenant': tenant,
            }
        )


class Tenant(object):

    @classmethod
    def autodetect(cls, tokens):
        token = tokens.from_headers()
        try:
            tenant = cls.from_headers()
        except InvalidTenant:
            return cls.from_token(token)

        try:
            return tenant.check_against(token)
        except InvalidTenant:
            raise UnauthorizedTenant(token)

    @classmethod
    def from_headers(cls):
        try:
            tenant_uuid = request.headers['X-Wazo-Tenant']
        except KeyError:
            raise InvalidTenant()
        return cls(uuid=tenant_uuid)

    @classmethod
    def from_token(cls, token):
        try:
            tenants = token['metadata']['tenants']
        except KeyError:
            raise InvalidTenant()
        if not tenants:
            raise InvalidTenant()
        if len(tenants) > 1:
            raise InvalidTenant()
        return cls(**tenants[0])

    def __init__(self, uuid, name=None):
        self.uuid = uuid
        self.name = name

    def check_against(self, token):
        authorized_tenants = (tenant['uuid'] for tenant in token['metadata'].get('tenants', []))
        if self.uuid not in authorized_tenants:
            raise InvalidTenant(self.uuid)
        return self


class Tokens(object):

    def __init__(self, auth):
        self._auth = auth

    def get(self, token_id):
        try:
            return self._auth.token.get(token_id)
        except requests.HTTPError as e:
            raise InvalidToken(token_id)
        except requests.RequestException as e:
            raise AuthServerUnreachable(self._auth.host, self._auth.port, e)

    def from_headers(self):
        token_id = extract_token_id_from_header()
        if not token_id:
            raise InvalidToken()
        return self.get(token_id)


class CachedTokens(Tokens):

    def get(self, token_id):
        token = flask.g['tokens'].get(token_id)
        if token:
            return token

        token = flask.g['tokens'][token_id] = super().get(token_id)
        return token
