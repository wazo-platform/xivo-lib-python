# Copyright 2018-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import logging
from typing import TypeVar

from flask import current_app, g
from wazo_auth_client import Client as AuthClient
from werkzeug.local import LocalProxy

from xivo.tenant_helpers import Token, User

from . import tenant_helpers

logger = logging.getLogger(__name__)


def get_auth_client() -> AuthClient:
    auth_client = g.get('auth_client')
    if not auth_client:
        auth_client = g.auth_client = AuthClient(**current_app.config['auth'])
    return auth_client


auth_client: AuthClient = LocalProxy(get_auth_client)


def get_token() -> Token:
    token = g.get('token')
    if not token:
        if g.get('token_extractor'):
            _token = Token(g.token_extractor(), auth_client)
        else:
            _token = Token.from_headers(auth_client)
        token = g.token = _token
        auth_client.set_token(token.uuid)
    return token


token: Token = LocalProxy(get_token)  # type: ignore[assignment]


def get_user() -> User:
    user = g.get('user')
    if not user:
        user = g.user = User(token.user_uuid)
    return user


user: User = LocalProxy(get_user)  # type: ignore[assignment]

Self = TypeVar('Self', bound='Tenant')


class Tenant(tenant_helpers.Tenant):
    @classmethod
    def autodetect(cls: type[Self], include_query: bool = False) -> Self:
        tenant = None
        if include_query:
            try:
                tenant = cls.from_query()
            except tenant_helpers.InvalidTenant:
                logger.debug('Invalid tenant from query, using header...')
            else:
                logger.debug('Found tenant "%s" from query', tenant.uuid)

        if not tenant:
            try:
                tenant = cls.from_headers()
            except tenant_helpers.InvalidTenant:
                logger.debug('Invalid tenant from header, using token...')
            else:
                logger.debug('Found tenant "%s" from header', tenant.uuid)

        if not tenant:
            tenant = cls.from_token(token)
            logger.debug('Found tenant "%s" from token', tenant.uuid)
            return tenant

        try:
            return tenant.check_against_token(token)
        except tenant_helpers.InvalidTenant:
            logger.debug('Tenant invalid against token')
            raise tenant_helpers.UnauthorizedTenant(tenant.uuid)
