# Copyright 2015-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import requests

from xivo import rest_api_helpers


class Unauthorized(rest_api_helpers.APIException):
    def __init__(self, token: str, required_access: str | None = None) -> None:
        details = {'invalid_token': token}
        if required_access:
            details['required_access'] = required_access

        super().__init__(
            status_code=401,
            message='Unauthorized',
            error_id='unauthorized',
            details=details,
        )


class InvalidTokenAPIException(rest_api_helpers.APIException):
    def __init__(self, token: str, required_access: str | None = None) -> None:
        details = {'invalid_token': token, 'reason': 'not_found_or_expired'}
        if required_access:
            details['required_access'] = required_access
        super().__init__(
            status_code=401,
            message='Unauthorized',
            error_id='unauthorized',
            details=details,
        )


class MissingPermissionsTokenAPIException(rest_api_helpers.APIException):
    def __init__(
        self,
        token: str,
        required_access: str | None,
        tenant_uuid: str | None,
    ) -> None:
        details = {
            'invalid_token': token,
            'reason': 'missing_permission_or_invalid_tenant',
            'required_access': required_access,
            'tenant_uuid': tenant_uuid,
        }
        super().__init__(
            status_code=401,
            message='Unauthorized',
            error_id='unauthorized',
            details=details,
        )


class AuthServerUnreachable(rest_api_helpers.APIException):
    def __init__(
        self, host: str | None, port: int | None, error: requests.RequestException
    ) -> None:
        super().__init__(
            status_code=503,
            message='Authentication server unreachable',
            error_id='authentication-server-unreachable',
            details={
                'auth_server_host': host,
                'auth_server_port': port,
                'original_error': str(error),
            },
        )
