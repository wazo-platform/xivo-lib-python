# Copyright 2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from unittest.mock import Mock, PropertyMock, patch
from unittest.mock import sentinel as s

import pytest

from xivo.auth_verifier import Unauthorized, no_auth, required_acl, required_tenant
from xivo.http_exceptions import InvalidTokenAPIException

from ..auth_verifier import AuthVerifierFlask


class TestAuthVerifierFlask(unittest.TestCase):
    def test_verify_token_decorator(self):
        mock_client = Mock(host=s.host, port=s.port)
        auth_verifier = AuthVerifierFlask()
        mock_token = Mock()
        mock_g = Mock()
        g_data = {
            'auth_client': mock_client,
            'token': mock_token,
            'token_extractor': None,
        }
        mock_g.get.side_effect = lambda x: g_data[x]
        tenant_extractor = Mock(return_value=s.tenant)

        @auth_verifier.verify_token
        @required_acl('foo')
        def decorated():
            return s.result

        with patch(
            'xivo.flask.auth_verifier.extract_tenant_id_from_header',
            tenant_extractor,
        ):
            with patch('xivo.flask.auth_verifier.g', mock_g):
                with patch('xivo.tenant_flask_helpers.g', mock_g):
                    result = decorated()

        assert result == s.result

    def test_verify_token_when_no_auth(self):
        auth_verifier = AuthVerifierFlask()

        @auth_verifier.verify_token
        @no_auth
        def decorated():
            return s.result

        result = decorated()

        assert result == s.result

    def test_verify_tenant_decorator(self):
        mock_client = Mock()
        auth_verifier = AuthVerifierFlask()
        mock_token = Mock(uuid=s.token, tenant_uuid=s.tenant)
        mock_g = Mock()
        g_data = {
            'auth_client': mock_client,
            'token': mock_token,
            'token_extractor': None,
        }
        mock_g.get.side_effect = lambda x: g_data[x]

        @auth_verifier.verify_tenant
        @required_tenant(s.tenant)
        def decorated():
            return s.result

        with patch('xivo.flask.auth_verifier.g', mock_g):
            with patch('xivo.tenant_flask_helpers.g', mock_g):
                result = decorated()

        assert result == s.result

    def test_verify_tenant_when_no_required_tenant(self):
        auth_verifier = AuthVerifierFlask()

        @auth_verifier.verify_tenant
        def decorated():
            return s.result

        result = decorated()

        assert result == s.result

    def test_verify_tenant_when_invalid_token(self):
        mock_client = Mock()
        auth_verifier = AuthVerifierFlask()
        mock_token = Mock(uuid=s.token)
        type(mock_token).tenant_uuid = PropertyMock(
            side_effect=InvalidTokenAPIException(s.token)
        )
        mock_g = Mock()
        g_data = {
            'auth_client': mock_client,
            'token': mock_token,
            'token_extractor': None,
        }
        mock_g.get.side_effect = lambda x: g_data[x]

        @auth_verifier.verify_tenant
        @required_tenant(s.tenant)
        def decorated():
            return s.result

        with patch('xivo.flask.auth_verifier.g', mock_g):
            with patch('xivo.tenant_flask_helpers.g', mock_g):
                with pytest.raises(Unauthorized) as exc_info:
                    decorated()

        assert exc_info.value.details['invalid_token'] == s.token
