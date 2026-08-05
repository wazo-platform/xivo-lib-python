# Copyright 2015-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from functools import lru_cache
from typing import TYPE_CHECKING, Any, NamedTuple, TypeVar

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

RESERVED_IDENTITY_WORDS = frozenset(('me', 'my_session'))
ACCESS_CACHE_SIZE = 4096
ACL_CACHE_SIZE = 2048


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


class _CompiledACL(NamedTuple):
    positive: tuple[re.Pattern, ...]
    negative: tuple[re.Pattern, ...]
    positive_reserved: tuple[re.Pattern, ...]
    negative_reserved: tuple[re.Pattern, ...]
    literal_ids: frozenset[str]


@lru_cache(maxsize=ACCESS_CACHE_SIZE)
def _compile_access(access: str) -> re.Pattern:
    access_regex = re.escape(access).replace('\\*', '[^.#]*?').replace('\\#', '.*?')
    access_regex = AccessCheck._replace_reserved_words(
        access_regex, ReservedWord('edit', 'update')
    )
    return re.compile(f'^{access_regex}$')


@lru_cache(maxsize=ACL_CACHE_SIZE)
def compile_acl(acl: frozenset[str]) -> _CompiledACL:
    positive: list[re.Pattern] = []
    negative: list[re.Pattern] = []
    positive_reserved: list[re.Pattern] = []
    negative_reserved: list[re.Pattern] = []
    literal_ids: set[str] = set()

    for entry in acl:
        negated = entry.startswith('!')
        access = entry[1:] if negated else entry
        segments = access.split('.')
        literal_ids.update(segments)
        regex = _compile_access(access)
        uses_reserved_word = bool(RESERVED_IDENTITY_WORDS.intersection(segments))
        if negated:
            negative.append(regex)
            if uses_reserved_word:
                negative_reserved.append(regex)
        else:
            positive.append(regex)
            if uses_reserved_word:
                positive_reserved.append(regex)

    return _CompiledACL(
        positive=tuple(positive),
        negative=tuple(negative),
        positive_reserved=tuple(positive_reserved),
        negative_reserved=tuple(negative_reserved),
        literal_ids=frozenset(literal_ids),
    )


class AccessCheck:
    def __init__(self, auth_id: str, session_id: str, acl: list[str]) -> None:
        self.auth_id = auth_id
        self._auth_id = str(auth_id)
        self._session_id = str(session_id)

        compiled = compile_acl(frozenset(acl))
        if compiled.literal_ids & {self._auth_id, self._session_id}:
            compiled = self._compile_per_caller(auth_id, session_id, acl)

        self._positive_access_regexes = compiled.positive
        self._negative_access_regexes = compiled.negative
        self._positive_reserved_regexes = compiled.positive_reserved
        self._negative_reserved_regexes = compiled.negative_reserved

    @classmethod
    def _compile_per_caller(
        cls, auth_id: str, session_id: str, acl: list[str]
    ) -> _CompiledACL:
        return _CompiledACL(
            positive=tuple(
                cls._transform_access_to_regex(auth_id, session_id, access)
                for access in acl
                if not access.startswith('!')
            ),
            negative=tuple(
                cls._transform_access_to_regex(auth_id, session_id, access[1:])
                for access in acl
                if access.startswith('!')
            ),
            positive_reserved=(),
            negative_reserved=(),
            literal_ids=frozenset(),
        )

    def _generalize_identity(self, required_access: str) -> str | None:
        if (
            self._auth_id not in required_access
            and self._session_id not in required_access
        ):
            return None
        generalized = '.'.join(
            'me'
            if segment == self._auth_id
            else 'my_session'
            if segment == self._session_id
            else segment
            for segment in required_access.split('.')
        )
        return generalized if generalized != required_access else None

    def matches_required_access(self, required_access: str | None) -> bool:
        if required_access is None:
            return True

        generalized = (
            self._generalize_identity(required_access)
            if self._positive_reserved_regexes or self._negative_reserved_regexes
            else None
        )

        for access_regex in self._negative_access_regexes:
            if access_regex.match(required_access):
                return False
        if generalized is not None:
            for access_regex in self._negative_reserved_regexes:
                if access_regex.match(generalized):
                    return False

        for access_regex in self._positive_access_regexes:
            if access_regex.match(required_access):
                return True
        if generalized is not None:
            for access_regex in self._positive_reserved_regexes:
                if access_regex.match(generalized):
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
