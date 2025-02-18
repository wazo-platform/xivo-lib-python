# Copyright 2024-2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

from flask import g

from ..auth_verifier import AuthVerifierHelpers
from ..http_exceptions import InvalidTokenAPIException, Unauthorized
from ..tenant_flask_helpers import auth_client, token
from .headers import extract_tenant_id_from_header, extract_token_id_from_header

R = TypeVar('R')


class AuthVerifierFlask:
    def __init__(self) -> None:
        self.helpers = AuthVerifierHelpers()

    def set_token_extractor(self, func: Callable[..., R]) -> None:
        endpoint_extract_token = self.helpers.extract_acl_check(func).extract_token_id
        service_extract_token = extract_token_id_from_header
        g.token_extractor = endpoint_extract_token or service_extract_token

    def verify_token(self, func: Callable[..., R]) -> Callable[..., R | None]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> R | None:
            if self.helpers.extract_no_auth(func):
                return func(*args, **kwargs)

            self.set_token_extractor(func)
            token_uuid = token.uuid
            required_acl = self.helpers.extract_required_acl(func, kwargs)
            tenant_uuid = extract_tenant_id_from_header() or None

            self.helpers.validate_token(
                auth_client,
                token_uuid,
                required_acl,
                tenant_uuid,
            )

            # NOTE: Used to efficiently retrieve endpoint's required ACL directly
            #       in request context, useful for hooks and plugins
            g.verified_acl = required_acl

            g.verified_tenant_uuid = tenant_uuid

            return func(*args, **kwargs)

        return wrapper

    def verify_tenant(self, func: Callable[..., R]) -> Callable[..., R]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            required_tenant = self.helpers.extract_required_tenant(func)
            if not required_tenant:
                return func(*args, **kwargs)

            self.set_token_extractor(func)

            try:
                tenant_uuid = token.tenant_uuid
            except InvalidTokenAPIException:
                raise Unauthorized(token.uuid)

            self.helpers.validate_tenant(required_tenant, tenant_uuid, token.uuid)
            return func(*args, **kwargs)

        return wrapper
