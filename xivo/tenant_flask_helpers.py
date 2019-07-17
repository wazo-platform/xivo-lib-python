# -*- coding: utf-8 -*-
# Copyright 2018-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging

from flask import current_app, g
from wazo_auth_client import Client as AuthClient
from werkzeug.local import LocalProxy
from xivo.tenant_helpers import Tokens, Users

from . import tenant_helpers

logger = logging.getLogger(__name__)


def get_auth_client():
    auth_client = g.get('auth_client')
    if not auth_client:
        auth_client = g.auth_client = AuthClient(**current_app.config['auth'])
    return auth_client


auth_client = LocalProxy(get_auth_client)


def get_token():
    token = g.get('token')
    if not token:
        token = g.token = Tokens(auth_client).from_headers()
        auth_client.set_token(token.uuid)
    return token


token = LocalProxy(get_token)


def get_current_user():
    current_user = g.get('current_user')
    if not current_user:
        auth_client.set_token(token.uuid)
        current_user = g.current_user = Users(auth_client).get(token.user_uuid)
    return current_user


current_user = LocalProxy(get_current_user)


class Tenant(tenant_helpers.Tenant):
    @classmethod
    def autodetect(cls):
        return cls.autodetect_one()

    @classmethod
    def autodetect_one(cls):
        try:
            tenant = cls.from_headers()
        except tenant_helpers.InvalidTenant:
            logger.debug('Invalid tenant from header, using token...')
            tenant = cls.from_token(token)
            logger.debug('Found tenant "%s" from token', tenant.uuid)
            return tenant

        logger.debug('Found tenant "%s" from header', tenant.uuid)
        try:
            return tenant.check_against_token(token)
        except tenant_helpers.InvalidTenant:
            logger.debug('Tenant invalid against token')
            raise tenant_helpers.UnauthorizedTenant(tenant.uuid)
