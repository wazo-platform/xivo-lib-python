# Copyright 2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import os

import requests
from hamcrest import assert_that, contains_string
from wazo_test_helpers.asset_launching_test_case import AssetLaunchingTestCase

ASSET_ROOT = os.path.join(os.path.dirname(__file__), '..', 'assets')


class _BaseTest(AssetLaunchingTestCase):
    assets_root = ASSET_ROOT
    service = 'wsgi-patch'
    asset = 'wsgi-patch'

    def test_wsgi_patch(self) -> None:
        server_ip = '127.0.0.1'
        service_port = self.service_port(8080, 'wsgi-patch')
        url = f'http://{server_ip}:{service_port}/resource'

        for i in range(150):
            try:
                requests.get(url, timeout=(1, 0.1))
            except Exception:
                pass
            if not self.service_status('wsgi-patch')['State']['Running']:
                break

        logs = self.service_logs('wsgi-patch')
        assert_that(logs, contains_string('OS Error'))

        container_running = self.service_status('wsgi-patch')['State']['Running']
        assert_that(not container_running)
