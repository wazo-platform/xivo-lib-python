# Copyright 2015-2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any, Callable, NamedTuple, TypeVar

import requests
from wazo_auth_client import exceptions

from .http_exceptions import (
    AuthServerUnreachable,
    InvalidTokenAPIException,
    MissingPermissionsTokenAPIException,
    Unauthorized,
)

if TYPE_CHECKING:
    from wazo_auth_client import Client as AuthClient

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


class AuthVerifierHelpers:
    def extract_acl_check(self, func: Callable[..., R]) -> _ACLCheck:
        # backward compatibility: when func.acl is not defined, it should
        # probably just raise an AttributeError
        return getattr(func, 'acl', _ACLCheck('', None))

    def extract_no_auth(self, func: Callable[..., R]) -> bool:
        return getattr(func, 'no_auth', False)

    def extract_required_acl(self, func: Callable[..., R], func_kwargs: Any) -> str:
        acl_check = self.extract_acl_check(func)
        return self._required_acl(acl_check, func_kwargs)

    def validate_token(
        self,
        auth_client: AuthClient,
        token_uuid: str,
        required_acl: str,
        tenant_uuid: str | None,
    ) -> None:
        try:
            token_is_valid = auth_client.token.check(
                token_uuid,
                required_acl,
                tenant=tenant_uuid,
            )
        except exceptions.InvalidTokenException:
            raise InvalidTokenAPIException(token_uuid, required_acl)
        except exceptions.MissingPermissionsTokenException:
            raise MissingPermissionsTokenAPIException(
                token_uuid,
                required_acl,
                tenant_uuid,
            )
        except requests.RequestException as error:
            raise AuthServerUnreachable(auth_client.host, auth_client.port, error)

        if not token_is_valid:
            raise NotImplementedError('Invalid token without exception')

        return None

    def extract_required_tenant(self, func: Callable[..., R]) -> str | None:
        return getattr(func, 'tenant_uuid', None)

    def validate_tenant(
        self,
        required_tenant: str | None,
        tenant_uuid: str | None,
        token_uuid: str,
    ) -> None:
        if required_tenant == tenant_uuid:
            return None

        raise Unauthorized(token_uuid)

    def _required_acl(self, acl_check: _ACLCheck, kwargs: dict[str, str]) -> str:
        escaped_kwargs = {k: str(v).replace('.', '_') for k, v in kwargs.items()}
        return str(acl_check.pattern).format(**escaped_kwargs)


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

    def may_remove_access(self, access_to_remove: str) -> bool:
        return self.matches_required_access(
            access_to_remove
            if not access_to_remove.startswith('!')
            else access_to_remove[1:]
        )

    @staticmethod
    def _transform_access_to_regex(
        auth_id: str, session_id: str, access: str
    ) -> re.Pattern:
        access_regex = re.escape(access).replace('\\*', '[^.#]*?').replace('\\#', '.*?')
        access_regex = AccessCheck._replace_reserved_words(
            access_regex,
            ReservedWord('me', auth_id),
            ReservedWord('my_session', session_id),
            ReservedWord('edit', 'update'),  # Compatibility for deprecated suffix
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
