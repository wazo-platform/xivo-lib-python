# -*- coding: utf-8 -*-
# Copyright 2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

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
    def autodetect(cls, many=False):
        if many:
            return cls.autodetect_many()
        return cls.autodetect_one()

    @classmethod
    def autodetect_one(cls):
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

    @classmethod
    def autodetect_many(cls):
        tenants = cls.from_headers(many=True)

        if not tenants:
            try:
                return current_user.tenants()
            except tenant_helpers.InvalidUser:
                # xivo_admin and xivo_service do not have a user uuid that can be fetched on /users
                return [Tenant(**tenant) for tenant in token['metadata'].get('tenants')]

        for tenant in tenants:
            try:
                tenant.check_against_token(token)
                continue
            except tenant_helpers.InvalidTenant:
                pass  # check against user

            try:
                tenant.check_against_user(current_user)
            except tenant_helpers.InvalidTenant:
                raise tenant_helpers.UnauthorizedTenant(tenant.uuid)

        return tenants
