# Copyright 2018-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

import requests

from xivo import rest_api_helpers
from xivo.auth_verifier import AuthServerUnreachable, extract_token_id_from_header

# Necessary to avoid a dependency in provd
try:
    from flask import request
except ImportError:
    pass

if TYPE_CHECKING:
    from .auth_verifier import Client


class InvalidTenant(Exception):
    def __init__(self, tenant_uuid: str | None = None) -> None:
        message = "Invalid tenant"
        if tenant_uuid:
            message = f'{message} "{tenant_uuid}"'
        super().__init__(message)


class InvalidToken(Exception):
    def __init__(self, token_id: str | None = None) -> None:
        message = "Invalid token"
        if token_id:
            message = f'{message} "{token_id}"'
        super().__init__(message)


class InvalidUser(Exception):
    def __init__(self, user_uuid: str) -> None:
        super().__init__(f'Invalid user "{user_uuid}"')


class UnauthorizedTenant(rest_api_helpers.APIException):
    def __init__(self, tenant_uuid: str) -> None:
        super().__init__(
            status_code=401,
            message='Unauthorized tenant',
            error_id='unauthorized-tenant',
            details={'tenant_uuid': str(tenant_uuid)},
        )


Self = TypeVar('Self', bound='Tenant')


class Tenant:
    @classmethod
    def autodetect(cls: type[Self], tokens: Tokens) -> Self:
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
    def from_query(cls: type[Self]) -> Self:
        try:
            tenant_uuid = request.args['tenant']
        except KeyError:
            raise InvalidTenant()
        return cls(uuid=tenant_uuid)

    @classmethod
    def from_headers(cls: type[Self]) -> Self:
        try:
            tenant_uuid = request.headers['Wazo-Tenant']
        except KeyError:
            raise InvalidTenant()
        return cls(uuid=tenant_uuid)

    @classmethod
    def from_token(cls: type[Self], token: Token) -> Self:
        if not token.tenant_uuid:
            raise InvalidTenant()
        return cls(uuid=token.tenant_uuid)

    def __init__(self, uuid: str, name: str | None = None) -> None:
        self.uuid = uuid
        self.name = name

    def check_against_token(self: Self, token: Token) -> Self:
        if self.uuid == token.tenant_uuid:
            return self
        if not token.visible_tenants(tenant_uuid=self.uuid):
            raise InvalidTenant(self.uuid)
        return self

    def __repr__(self) -> str:
        result = f'<Tenant: {self.uuid}>'
        if self.name:
            result = f'<Tenant: {self.uuid} "{self.name}">'
        return result


class Tokens:
    def __init__(self, auth: Client):
        self._auth = auth

    def get(self, token_id: str) -> Token:
        try:
            return Token(self._auth.token.get(token_id), self._auth)
        except requests.HTTPError:
            raise InvalidToken(token_id)
        except requests.RequestException as e:
            raise AuthServerUnreachable(self._auth.host, self._auth.port, e)

    def from_headers(self) -> Token:
        token_id = extract_token_id_from_header()
        if not token_id:
            raise InvalidToken()
        return self.get(token_id)


class Token:
    def __init__(self, token_dict: dict[str, Any], auth: Client) -> None:
        self._auth = auth
        self._token_dict = token_dict
        self._cache_tenants: dict[str, list[Tenant]] = {}

    @property
    def uuid(self) -> str:
        return self._token_dict['token']

    @property
    def infos(self) -> dict[str, Any]:
        return dict(self._token_dict)

    @property
    def tenant_uuid(self) -> str | None:
        return self._token_dict['metadata'].get('tenant_uuid')

    @property
    def user_uuid(self) -> str | None:
        return self._token_dict['metadata'].get('uuid')

    def visible_tenants(self, tenant_uuid: str | None = None) -> list[Tenant]:
        if not tenant_uuid:
            tenant_uuid = self.tenant_uuid

        if not tenant_uuid:
            return []

        cached_tenant = self._cache_tenants.get(tenant_uuid)
        if cached_tenant:
            return cached_tenant

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

        tenants = [Tenant(t['uuid'], t['name']) for t in tenants_list]
        self._cache_tenants = {tenant_uuid: tenants}
        return tenants


class Users:
    def __init__(self, auth: Client) -> None:
        self._auth = auth

    def get(self, user_uuid: str | None) -> User:
        return User(self._auth, user_uuid)


class User:
    def __init__(self, auth: Client, uuid: str | None, **kwargs: Any) -> None:
        self._auth = auth
        self._uuid = uuid
        self._tenants = None
