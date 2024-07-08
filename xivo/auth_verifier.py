# Copyright 2015-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import logging
import re
from functools import wraps
from typing import Any, Callable, NamedTuple, NoReturn, TypeVar

import requests

from .http.exceptions import (
    AuthServerUnreachable,
    InvalidTokenAPIException,
    MissingPermissionsTokenAPIException,
    Unauthorized,
)
from .http.headers import (
    extract_token_id_from_header,
    extract_token_id_from_query_or_header,
    extract_token_id_from_query_string,
)

# Compatibility with old import
__all__ = [
    'extract_token_id_from_query_string',
    'extract_token_id_from_query_or_header',
]

# Postpone the raise to the first use of the Client constructor.
# wazo-auth uses its own version of the client to avoid using its own
# rest-api to call itself.
try:
    from wazo_auth_client import Client, exceptions
except ImportError as e:

    class Client:  # type: ignore[no-redef]
        _exc: Exception = e

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise self._exc


from flask import g

from .tenant_flask_helpers import token

logger = logging.getLogger(__name__)

F = TypeVar('F', bound=Callable[..., Any])
R = TypeVar('R')


class _ACLCheck(NamedTuple):
    pattern: str
    extract_token_id: Callable[[], str] | None


def required_acl(
    acl_pattern: str, extract_token_id: Callable[[], str] | None = None
) -> Callable[[F], F]:
    def wrapper(func: F) -> F:
        func.acl = _ACLCheck(acl_pattern, extract_token_id)  # type: ignore[attr-defined]
        return func

    return wrapper


def no_auth(func: F) -> F:
    func.no_auth = True  # type: ignore[attr-defined]
    return func


def required_tenant(tenant_uuid: str) -> Callable[[F], F]:
    def wrapper(func: F) -> F:
        func.tenant_uuid = tenant_uuid  # type: ignore[attr-defined]
        return func

    return wrapper


class AuthVerifier:
    def __init__(
        self,
        auth_config: dict[str, Any] | None = None,
        extract_token_id: Callable[[], str] | None = None,
    ) -> None:
        if extract_token_id is None:
            extract_token_id = extract_token_id_from_header
        self._auth_client: Client | None = None
        self._auth_config = auth_config
        self._extract_token_id = extract_token_id
        self._fallback_acl_check = _ACLCheck('', None)

    def set_config(self, auth_config: dict[str, Any]) -> None:
        self._auth_config = dict(auth_config)
        self._auth_config.pop('username', None)
        self._auth_config.pop('password', None)
        self._auth_config.pop('key_file', None)

    def set_client(self, auth_client: Client) -> None:
        self._auth_client = auth_client

    def verify_token(self, func: Callable[..., R]) -> Callable[..., R | None]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> R | None:
            no_auth: bool = getattr(func, 'no_auth', False)
            if no_auth:
                return func(*args, **kwargs)

            # backward compatibility: when func.acl is not defined, it should
            # probably just raise an AttributeError
            acl_check = getattr(func, 'acl', self._fallback_acl_check)
            self._set_extract_token_function(
                acl_check.extract_token_id,
                self._extract_token_id,
            )
            required_acl = self._required_acl(acl_check, args, kwargs)
            try:
                token_is_valid = self.client().token.check(token.uuid, required_acl)
            except exceptions.InvalidTokenException:
                return self._handle_invalid_token_exception(
                    token.uuid, required_access=required_acl
                )
            except exceptions.MissingPermissionsTokenException:
                return self._handle_missing_permissions_token_exception(
                    token.uuid, required_access=required_acl
                )
            except requests.RequestException as e:
                return self.handle_unreachable(e)

            if not token_is_valid:
                raise NotImplementedError('Invalid token without exception')

            return func(*args, **kwargs)

        return wrapper

    def _set_extract_token_function(
        self,
        specific_extractor: Callable[[], str] | None,
        default_extractor: Callable[[], str] | None = None,
    ) -> None:
        g.token_extractor = specific_extractor or default_extractor

    def verify_tenant(self, func: Callable[..., R]) -> Callable[..., R]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            required_tenant = getattr(func, 'tenant_uuid', None)
            if not required_tenant:
                return func(*args, **kwargs)
            self._set_extract_token_function(self._extract_token_id)

            try:
                tenant_uuid = token.tenant_uuid
            except InvalidTokenAPIException as e:
                return self.handle_unauthorized(e.details['invalid_token'])
            except AuthServerUnreachable as e:
                return self.handle_unreachable(e.details['original_error'])

            if required_tenant == tenant_uuid:
                return func(*args, **kwargs)

            return self.handle_unauthorized(token.uuid)

        return wrapper

    def _required_acl(
        self, acl_check: _ACLCheck, args: Any, kwargs: dict[str, str]
    ) -> str:
        escaped_kwargs = {
            key: str(value).replace('.', '_') for key, value in kwargs.items()
        }
        return str(acl_check.pattern).format(**escaped_kwargs)

    def handle_unreachable(self, error: requests.RequestException) -> NoReturn:
        host: str | None = None
        port: int | None = None

        if self._auth_config:
            host, port = self._auth_config['host'], self._auth_config['port']
        raise AuthServerUnreachable(host, port, error)

    def handle_unauthorized(
        self, token: str, required_access: str | None = None
    ) -> NoReturn:
        raise Unauthorized(token, required_access)

    def _handle_invalid_token_exception(
        self, token: str, required_access: str | None = None
    ) -> NoReturn:
        raise InvalidTokenAPIException(token, required_access)

    def _handle_missing_permissions_token_exception(
        self, token: str, required_access: str | None = None
    ) -> NoReturn:
        raise MissingPermissionsTokenAPIException(token, required_access)

    def client(self) -> Client:
        if not (self._auth_config or self._auth_client):
            raise RuntimeError('AuthVerifier is not configured')

        if not self._auth_client:
            self._auth_client = Client(**self._auth_config)
        return self._auth_client


class AccessCheck:
    def __init__(self, auth_id: str, session_id: str, acl: list[str]) -> None:
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

    def matches_required_access(self, required_access: str | None) -> bool:
        if required_access is None:
            return True

        for access_regex in self._negative_access_regexes:
            if access_regex.match(required_access):
                return False

        for access_regex in self._positive_access_regexes:
            if access_regex.match(required_access):
                return True
        return False

    def may_add_access(self, new_access: str) -> bool:
        return new_access.startswith('!') or self.matches_required_access(new_access)

    @staticmethod
    def _transform_access_to_regex(
        auth_id: str, session_id: str, access: str
    ) -> re.Pattern:
        access_regex = re.escape(access).replace('\\*', '[^.#]*?').replace('\\#', '.*?')
        access_regex = AccessCheck._replace_reserved_words(
            access_regex,
            ReservedWord('me', auth_id),
            ReservedWord('my_session', session_id),
        )
        return re.compile(f'^{access_regex}$')

    @staticmethod
    def _replace_reserved_words(
        access_regex: str, *reserved_words: ReservedWord
    ) -> str:
        words = access_regex.split('\\.')
        for reserved_word in reserved_words:
            words = [reserved_word.replace(word) for word in words]
        return '\\.'.join(words)


class ReservedWord:
    def __init__(self, word: str, value: str) -> None:
        self._reserved_word = word
        self._replacement = f'({word}|{value})'

    def replace(self, word: str) -> str:
        return self._replacement if word == self._reserved_word else word
