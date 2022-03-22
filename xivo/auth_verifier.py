# -*- coding: utf-8 -*-
# Copyright 2015-2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import re
import requests

from collections import namedtuple
from functools import wraps
from six import iteritems, text_type

# Necessary to avoid a dependency in provd
try:
    from flask import request
except ImportError:
    pass

# Postpone the raise to the first use of the Client constructor.
# wazo-auth uses its own version of the client to avoid using its own
# rest-api to call itself.
try:
    from wazo_auth_client import Client
except ImportError as e:

    class Client(object):
        _exc = e

        def __init__(self, *args, **kwargs):
            raise self._exc


from xivo import rest_api_helpers

_ACLCheck = namedtuple('_ACLCheck', ['pattern', 'extract_token_id'])
logger = logging.getLogger(__name__)


def required_acl(acl_pattern, extract_token_id=None):
    def wrapper(func):
        func.acl = _ACLCheck(acl_pattern, extract_token_id)
        return func

    return wrapper


def no_auth(func):
    func.no_auth = True
    return func


def required_tenant(tenant_uuid):
    def wrapper(func):
        func.tenant_uuid = tenant_uuid
        return func

    return wrapper


class Unauthorized(rest_api_helpers.APIException):
    def __init__(self, token, required_access=None):
        details = {'invalid_token': token}
        if required_access:
            details['required_access'] = required_access
        super(Unauthorized, self).__init__(
            status_code=401,
            message='Unauthorized',
            error_id='unauthorized',
            details=details,
        )


class Invalid_Token_Exception(rest_api_helpers.APIException):
    def __init__(self, token, required_access=None, cause=None):
        details = {'invalid_token': token}
        if required_access:
            details['required_access'] = required_access
        if cause:
            details['reason'] = cause
        super(Invalid_Token_Exception, self).__init__(
            status_code=401,
            message='Unauthorized',
            error_id='unauthorized',
            details=details,
        )


class Missing_Permissions_Token_Exception(rest_api_helpers.APIException):
    def __init__(self, token, required_access=None, cause=None):
        details = {'invalid_token': token}
        if required_access:
            details['required_access'] = required_access
        if cause:
            details['reason'] = cause
        super(Missing_Permissions_Token_Exception, self).__init__(
            status_code=401,
            message='Unauthorized',
            error_id='unauthorized',
            details=details,
        )


class AuthServerUnreachable(rest_api_helpers.APIException):
    def __init__(self, host, port, error):
        super(AuthServerUnreachable, self).__init__(
            status_code=503,
            message='Authentication server unreachable',
            error_id='authentication-server-unreachable',
            details={
                'auth_server_host': host,
                'auth_server_port': port,
                'original_error': str(error),
            },
        )


class AuthVerifier(object):
    def __init__(self, auth_config=None, extract_token_id=None):
        if extract_token_id is None:
            extract_token_id = extract_token_id_from_header
        self._auth_client = None
        self._auth_config = auth_config
        self._extract_token_id = extract_token_id
        self._fallback_acl_check = _ACLCheck('', None)

    def set_config(self, auth_config):
        self._auth_config = dict(auth_config)
        self._auth_config.pop('username', None)
        self._auth_config.pop('password', None)
        self._auth_config.pop('key_file', None)

    def set_client(self, auth_client):
        self._auth_client = auth_client

    def verify_token(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            no_auth = getattr(func, 'no_auth', False)
            if no_auth:
                return func(*args, **kwargs)

            # backward compatibility: when func.acl is not defined, it should
            # probably just raise an AttributeError
            acl_check = getattr(func, 'acl', self._fallback_acl_check)
            self._add_request_properties((acl_check.extract_token_id or self.token)())
            required_acl = self._required_acl(acl_check, args, kwargs)
            try:
                token_is_valid = self.client().token.is_valid(
                    request.token_id, required_acl
                )
            except requests.RequestException as e:
                return self.handle_unreachable(e)

            if token_is_valid:
                return func(*args, **kwargs)

            return self.handle_unauthorized(
                request.token_id, required_access=required_acl
            )

        return wrapper

    def _add_request_properties(self, token_id):
        request.token_id = token_id
        request._get_token_content = self._get_token_content
        request._get_user_uuid = self._get_user_uuid
        request.__class__.token_content = property(
            lambda this: this._get_token_content()
        )
        request.__class__.user_uuid = property(lambda this: this._get_user_uuid())

    def _get_token_content(self):
        if not hasattr(request, '_token_content'):
            request._token_content = self.client().token.get(request.token_id)
        return request._token_content

    def _get_user_uuid(self):
        return request.token_content.get('metadata', {}).get('uuid')

    def verify_tenant(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            required_tenant = getattr(func, 'tenant_uuid', None)
            if not required_tenant:
                return func(*args, **kwargs)
            self._add_request_properties(self.token())

            try:
                token = request.token_content
            except requests.RequestException as e:
                if e.response is not None and e.response.status_code == 404:
                    return self.handle_unauthorized(request.token_id)
                return self.handle_unreachable(e)

            tenant_uuid = token.get('metadata', {}).get('tenant_uuid')
            if required_tenant == tenant_uuid:
                return func(*args, **kwargs)

            return self.handle_unauthorized(request.token_id)

        return wrapper

    def token(self):
        return self._extract_token_id()

    def _required_acl(self, acl_check, args, kwargs):
        escaped_kwargs = {
            key: text_type(value).replace(u'.', u'_')
            for key, value in iteritems(kwargs)
        }
        return text_type(acl_check.pattern).format(**escaped_kwargs)

    def handle_unreachable(self, error):
        raise AuthServerUnreachable(
            self._auth_config['host'], self._auth_config['port'], error
        )

    def handle_unauthorized(self, token, required_access=None):
        raise Unauthorized(token, required_access)

    def _handle_invalid_token_exception(self, token, required_access=None):
        raise Invalid_Token_Exception(token, required_access, 'not_found_or_expired')

    def _handle_missing_permissions_token_exception(self, token, required_access=None):
        raise Missing_Permissions_Token_Exception(
            token, required_access, 'missing_permission'
        )

    def client(self):
        if not (self._auth_config or self._auth_client):
            raise RuntimeError('AuthVerifier is not configured')

        if not self._auth_client:
            self._auth_client = Client(**self._auth_config)
        return self._auth_client


def extract_token_id_from_header():
    return request.headers.get('X-Auth-Token', '')


def extract_token_id_from_query_string():
    return request.args.get('token', '')


def extract_token_id_from_query_or_header():
    return extract_token_id_from_query_string() or extract_token_id_from_header()


class AccessCheck:
    def __init__(self, auth_id, session_id, acl):
        self.auth_id = auth_id
        self._positive_access_regexes = [
            self._transform_access_to_regex(auth_id, session_id, access)
            for access in acl
            if not access.startswith('!')
        ]
        self._negative_access_regexes = [
            self._transform_access_to_regex(auth_id, session_id, access[1:])
            for access in acl
            if access.startswith('!')
        ]

    def matches_required_access(self, required_access):
        if required_access is None:
            return True

        for access_regex in self._negative_access_regexes:
            if access_regex.match(required_access):
                return False

        for access_regex in self._positive_access_regexes:
            if access_regex.match(required_access):
                return True
        return False

    def may_add_access(self, new_access):
        return new_access.startswith('!') or self.matches_required_access(new_access)

    @staticmethod
    def _transform_access_to_regex(auth_id, session_id, access):
        access_regex = re.escape(access).replace('\\*', '[^.#]*?').replace('\\#', '.*?')
        access_regex = AccessCheck._replace_reserved_words(
            access_regex,
            ReservedWord('me', auth_id),
            ReservedWord('my_session', session_id),
        )
        return re.compile('^{}$'.format(access_regex))

    @staticmethod
    def _replace_reserved_words(access_regex, *reserved_words):
        words = access_regex.split('\\.')
        for reserved_word in reserved_words:
            words = tuple(reserved_word.replace(word) for word in words)
        return '\\.'.join(words)


class ReservedWord:
    def __init__(self, word, value):
        self._reserved_word = word
        self._replacement = '({word}|{value})'.format(word=word, value=value)

    def replace(self, word):
        return self._replacement if word == self._reserved_word else word
