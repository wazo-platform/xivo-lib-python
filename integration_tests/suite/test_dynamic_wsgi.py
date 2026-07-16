# Copyright 2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from concurrent.futures import ThreadPoolExecutor

import requests
from hamcrest import assert_that, contains_string, equal_to
from wazo_test_helpers import until
from wazo_test_helpers.asset_launching_test_case import AssetLaunchingTestCase

ASSET_ROOT = os.path.join(os.path.dirname(__file__), '..', 'assets')


class TestDynamicWSGIServer(AssetLaunchingTestCase):
    assets_root = ASSET_ROOT
    service = 'dynamic-wsgi'
    asset = 'dynamic-wsgi'

    def test_pool_grows_under_load_and_shrinks_after(self) -> None:
        server_ip = '127.0.0.1'
        service_port = self.service_port(8080, 'dynamic-wsgi')
        url = f'http://{server_ip}:{service_port}/slow'

        # numthreads=2: 5 concurrent slow requests force the pool to grow.
        with self.capture_logs('dynamic-wsgi') as logs:
            with ThreadPoolExecutor(max_workers=5) as pool:
                futures = [pool.submit(requests.get, url, timeout=10) for _ in range(5)]
                for future in futures:
                    response = future.result()
                    assert_that(response.status_code, equal_to(200))

        assert_that(logs.result(), contains_string('WSGI thread pool grown'))

        def shrunk() -> None:
            assert_that(
                self.service_logs('dynamic-wsgi'),
                contains_string('WSGI thread pool shrink requested'),
            )

        until.assert_(shrunk, tries=10, interval=1)
