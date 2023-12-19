# Copyright 2018-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import os

from hamcrest import assert_that, contains_string
from wazo_test_helpers.asset_launching_test_case import AssetLaunchingTestCase

ASSET_ROOT = os.path.join(os.path.dirname(__file__), '..', 'assets')


class _BaseTest(AssetLaunchingTestCase):
    assets_root = ASSET_ROOT
    service = 'thread-exception'
    asset = 'thread-exception'

    def test_thread_exception_is_logged(self):
        logs = self.service_logs('thread-exception')

        assert_that(logs, contains_string('exception is logged'))
