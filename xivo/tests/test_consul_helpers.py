# -*- coding: utf-8 -*-

# Copyright (C) 2015 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import unittest

from hamcrest import assert_that, equal_to
from mock import ANY, patch, sentinel as s

from ..consul_helpers import Registerer


class TestConsulRegisterer(unittest.TestCase):

    def setUp(self):
        self.service_name = 'my-service'
        self.registerer = Registerer(name=self.service_name, host=s.consul_host, port=s.consul_port,
                                     token=s.consul_token, advertise_address=s.advertise_address,
                                     advertise_port=s.advertise_port, check_url=s.check_url,
                                     check_url_timeout=s.check_url_timeout, service_tags=s.tags)

    @patch('xivo.consul_helpers.Consul')
    def test_that_register_calls_agent_register(self, Consul):
        consul_client = Consul.return_value

        self.registerer.register()

        Consul.assert_called_once_with(s.consul_host, s.consul_port, s.consul_token)
        consul_client.agent.service.register.assert_called_once_with(self.service_name,
                                                                     service_id=ANY,
                                                                     port=s.advertise_port,
                                                                     address=s.advertise_address,
                                                                     check=ANY, tags=s.tags)

    @patch('xivo.consul_helpers.Consul')
    @patch('xivo.consul_helpers.Check')
    def test_that_register_calls_adds_a_check(self, Check, Consul):
        consul_client = Consul.return_value
        http_check = Check.http.return_value

        self.registerer.register()

        Check.http.assert_called_once_with(s.check_url, s.check_url_timeout)
        consul_client.agent.service.register.assert_called_once_with(self.service_name,
                                                                     service_id=ANY,
                                                                     port=ANY,
                                                                     address=ANY,
                                                                     check=http_check,
                                                                     tags=ANY)

    @patch('xivo.consul_helpers.Consul')
    def test_that_deregister_calls_agent_deregister_service(self, Consul):
        consul_client = Consul.return_value

        self.registerer.deregister()

        Consul.assert_called_once_with(s.consul_host, s.consul_port, s.consul_token)
        consul_client.agent.service.deregister.assert_called_once_with(self.registerer._service_id)

    @patch('xivo.consul_helpers.Consul')
    def test_is_registered(self, Consul):
        consul_client = Consul.return_value

        service_id = self.registerer._service_id

        consul_client.catalog.service.return_value = (s.index, [{'ServiceName': self.service_name,
                                                                 'ServiceID': service_id}])

        result = self.registerer.is_registered()

        assert_that(result, equal_to(True))
