# -*- coding: utf-8 -*-
# Copyright 2018-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import requests

from xivo import rest_api_helpers
from xivo.auth_verifier import extract_token_id_from_header
from xivo.auth_verifier import AuthServerUnreachable

# Necessary to avoid a dependency in provd
try:
    from flask import request
except ImportError:
    pass


class InvalidTenant(Exception):
    def __init__(self, tenant_uuid=None):
        if tenant_uuid:
            super(InvalidTenant, self).__init__(
                'Invalid tenant "{uuid}"'.format(uuid=tenant_uuid)
            )
        else:
            super(InvalidTenant, self).__init__('Invalid tenant')


class InvalidToken(Exception):
    def __init__(self, token_id=None):
        if token_id:
            super(InvalidToken, self).__init__(
                'Invalid token "{id}"'.format(id=token_id)
            )
        else:
            super(InvalidToken, self).__init__('Invalid token')


class InvalidUser(Exception):
    def __init__(self, user_uuid):
        super(InvalidUser, self).__init__(
            'Invalid user "{uuid}"'.format(uuid=user_uuid)
        )


class UnauthorizedTenant(rest_api_helpers.APIException):
    def __init__(self, tenant_uuid):
        super(UnauthorizedTenant, self).__init__(
            status_code=401,
            message='Unauthorized tenant',
            error_id='unauthorized-tenant',
            details={'tenant_uuid': str(tenant_uuid)},
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
            return tenant.check_against_token(token)
        except InvalidTenant:
            raise UnauthorizedTenant(tenant.uuid)

    @classmethod
    def from_headers(cls):
        return cls.from_headers_one()

    @classmethod
    def from_headers_one(cls):
        try:
            tenant_uuid = request.headers['Wazo-Tenant']
        except KeyError:
            raise InvalidTenant()
        if ',' in tenant_uuid:
            raise InvalidTenant()
        return cls(uuid=tenant_uuid)

    @classmethod
    def from_token(cls, token):
        if not token.tenant_uuid:
            raise InvalidTenant()
        return cls(uuid=token.tenant_uuid)

    def __init__(self, uuid, name=None):
        self.uuid = uuid
        self.name = name

    def check_against_token(self, token):
        if self.uuid == token.tenant_uuid:
            return self
        visible_tenants = (tenant.uuid for tenant in token.visible_tenants())
        if self.uuid not in visible_tenants:
            raise InvalidTenant(self.uuid)
        return self

    def __repr__(self):
        result = '<Tenant: {uuid}>'.format(uuid=self.uuid)
        if self.name:
            result = '<Tenant: {uuid} "{name}">'.format(uuid=self.uuid, name=self.name)
        return result


class Tokens(object):
    def __init__(self, auth):
        self._auth = auth

    def get(self, token_id):
        try:
            return Token(self._auth.token.get(token_id), self._auth)
        except requests.HTTPError:
            raise InvalidToken(token_id)
        except requests.RequestException as e:
            raise AuthServerUnreachable(self._auth.host, self._auth.port, e)

    def from_headers(self):
        token_id = extract_token_id_from_header()
        if not token_id:
            raise InvalidToken()
        return self.get(token_id)


class Token(object):
    def __init__(self, token_dict, auth):
        self._auth = auth
        self._token_dict = token_dict

    @property
    def uuid(self):
        return self._token_dict['token']

    @property
    def infos(self):
        return dict(self._token_dict)

    @property
    def tenant_uuid(self):
        return self._token_dict['metadata'].get('tenant_uuid')

    @property
    def user_uuid(self):
        return self._token_dict['metadata'].get('uuid')

    def visible_tenants(self, tenant_uuid=None):
        if not tenant_uuid:
            tenant_uuid = self.tenant_uuid

        if not tenant_uuid:
            return []

        try:
            tenants_list = self._auth.tenants.list(tenant_uuid)['items']
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 401:
                if self.tenant_uuid == tenant_uuid:
                    return [Tenant(tenant_uuid)]
                else:
                    raise InvalidTenant(tenant_uuid)
            raise
        except requests.RequestException as e:
            raise AuthServerUnreachable(self._auth.host, self._auth.port, e)

        return [Tenant(tenant['uuid'], tenant['name']) for tenant in tenants_list]


class Users(object):
    def __init__(self, auth):
        self._auth = auth

    def get(self, user_uuid):
        return User(self._auth, user_uuid)


class User(object):
    def __init__(self, auth, uuid, **kwargs):
        self._auth = auth
        self._uuid = uuid
        self._tenants = None
