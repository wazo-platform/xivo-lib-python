# -*- coding: utf-8 -*-

# Copyright 2018 The Wazo Authors  (see the AUTHORS file)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from flask import (
    current_app,
    g,
)
from xivo_auth_client import Client as AuthClient
from werkzeug.local import LocalProxy
from xivo.tenant_helpers import Tokens, Users

from . import tenant_helpers


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
    return token


token = LocalProxy(get_token)


def get_current_user():
    current_user = g.get('current_user')
    if not current_user:
        auth_client.set_token(token['token'])
        current_user = g.current_user = Users(auth_client).get(token['metadata'].get('uuid'))
    return current_user


current_user = LocalProxy(get_current_user)


class Tenant(tenant_helpers.Tenant):
    @classmethod
    def autodetect(cls):
        try:
            tenant = cls.from_headers()
        except tenant_helpers.InvalidTenant:
            return cls.from_token(token)

        try:
            return tenant.check_against_token(token)
        except tenant_helpers.InvalidTenant:
            pass  # check against user

        try:
            return tenant.check_against_user(current_user)
        except tenant_helpers.InvalidTenant:
            raise tenant_helpers.UnauthorizedTenant(tenant.uuid)
