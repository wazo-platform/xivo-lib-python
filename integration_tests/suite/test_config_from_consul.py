# -*- coding: utf-8 -*-
# Copyright 2016-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later


import os
import requests

from consul import Consul
from hamcrest import assert_that, equal_to
from xivo_test_helpers.asset_launching_test_case import AssetLaunchingTestCase


ASSET_ROOT = os.path.join(os.path.dirname(__file__), '..', 'assets')


class TestConfigFromConsul(AssetLaunchingTestCase):

    assets_root = ASSET_ROOT
    asset = 'config-from-consul'
    service = 'xivo'

    def test_config_is_propagated(self):
        app_port = self.service_port(6363, service_name='config-from-consul')
        config = requests.get("http://localhost:{}/0.1/config".format(app_port)).json()
        expected_config = {
            'config_file': '/etc/config-from-consul/config.yml',
            'extra_config_files': '/etc/config-from-consul/conf.d',
        }
        assert_that(config, equal_to(expected_config))

        consul_port = self.service_port(8500, service_name='consul')
        client = Consul(host="localhost", port=consul_port, scheme="http")
        client.kv.put("config-from-consul/rest_api/listen", "0.0.0.0")
        client.kv.put("config-from-consul/rest_api/port", "6363")
        client.kv.put("other_service/rest_api/port", "1234")

        self.restart_service('config-from-consul')

        app_port = self.service_port(6363, service_name='config-from-consul')
        config = requests.get("http://localhost:{}/0.1/config".format(app_port)).json()

        expected_config['rest_api'] = {'listen': '0.0.0.0', 'port': '6363'}

        assert_that(config, equal_to(expected_config))

    def test_service_dont_exist(self):
        pass
