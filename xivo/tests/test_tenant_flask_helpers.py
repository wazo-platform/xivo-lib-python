# Copyright 2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from unittest.mock import Mock, patch
from unittest.mock import sentinel as s

from ..tenant_flask_helpers import auth_client as auth_client_proxy


class TestAuthClient(unittest.TestCase):
    @patch('xivo.tenant_flask_helpers.AuthClient')
    def test_config_deleted(self, auth_client):
        g_mock = Mock()
        g_mock.get.return_value = None
        config = {
            'host': s.host,
            'username': s.username,
            'password': s.password,
            'key_file': s.key_file,
        }
        current_app_mock = Mock(config={'auth': config})

        with patch('xivo.tenant_flask_helpers.current_app', current_app_mock):
            with patch('xivo.tenant_flask_helpers.g', g_mock):
                auth_client_proxy.host

        expected_config = {'host': s.host}
        auth_client.assert_called_once_with(**expected_config)
