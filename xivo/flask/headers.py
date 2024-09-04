# Copyright 2015-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from flask import request


def extract_token_id_from_header() -> str:
    return request.headers.get('X-Auth-Token', '')


def extract_token_id_from_query_string() -> str:
    return request.args.get('token', '')


def extract_token_id_from_query_or_header() -> str:
    return extract_token_id_from_query_string() or extract_token_id_from_header()


def extract_tenant_id_from_header() -> str:
    return request.headers.get('Wazo-Tenant', '')
