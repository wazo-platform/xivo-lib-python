# -*- coding: utf-8 -*-

# Copyright (C) 2015-2016 Avencall
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
import uuid

from hamcrest import assert_that, equal_to
from mock import ANY, patch, Mock, sentinel as s
from xivo_bus.resources.services import event


from ..consul_helpers import (NotifyingRegisterer,
                              Registerer,
                              RegistererError)


UUID = str(uuid.uuid4())
BUS_CONFIG = {'username': 'bus_username',
              'password': 'bus_password',
              'host': 'localhost',
              'port': 5532,
              'exchange_name': 'xchange',
              'exchange_type': 'topic'}


class TestNotifyingRegisterer(unittest.TestCase):

    def setUp(self):
        self.service_name = 'foobar'
        consul_config = {'host': s.consul_host,
                         'port': s.consul_port,
                         'token': s.consul_token}
        service_discovery_config = {'advertise_port': 4242,
                                    'advertise_address': 'localhost',
                                    'ttl_interval': 10,
                                    'extra_tags': []}
        self.registerer = NotifyingRegisterer(self.service_name,
                                              UUID,
                                              consul_config,
                                              service_discovery_config,
                                              BUS_CONFIG)
        self.service_id = self.registerer._service_id

    @patch('xivo.consul_helpers.Consul', Mock())
    def test_that_register_sends_a_service_registered_event_when_registered(self):
        with patch.object(self.registerer, '_send_msg') as send_msg:
            self.registerer.register()

            expected_message = event.ServiceRegisteredEvent(self.service_name,
                                                            self.service_id,
                                                            'localhost',
                                                            4242,
                                                            [UUID, self.service_name])

            send_msg.assert_called_once_with(expected_message)

    @patch('xivo.consul_helpers.Consul')
    def test_that_deregister_sends_a_service_deregistered_event_when_registered(self, Consul):
        consul_client = Consul.return_value
        consul_client.agent.service.deregister.return_value = True

        with patch.object(self.registerer, '_send_msg') as send_msg:
            self.registerer.deregister()

        expected_message = event.ServiceDeregisteredEvent(self.service_name,
                                                          self.service_id,
                                                          [UUID, self.service_name])

        send_msg.assert_called_once_with(expected_message)

    @patch('xivo.consul_helpers.Consul')
    def test_that_deregister_sends_a_service_deregistered_event_when_not_registered(self, Consul):
        consul_client = Consul.return_value
        consul_client.agent.service.deregister.return_value = False

        with patch.object(self.registerer, '_send_msg') as send_msg:
            self.registerer.deregister()
            assert_that(send_msg.call_count, equal_to(0))


class TestConsulRegisterer(unittest.TestCase):

    def setUp(self):
        self.service_name = 'my-service'
        consul_config = {'host': s.consul_host,
                         'port': s.consul_port,
                         'token': s.consul_token}
        service_discovery_config = {'advertise_address': s.advertise_address,
                                    'advertise_port': s.advertise_port,
                                    'ttl_interval': 10,
                                    'extra_tags': []}
        self.registerer = Registerer(self.service_name,
                                     UUID,
                                     consul_config,
                                     service_discovery_config)

    @patch('xivo.consul_helpers.Consul')
    def test_that_register_calls_agent_register(self, Consul):
        consul_client = Consul.return_value

        self.registerer.register()

        Consul.assert_called_once_with(host=s.consul_host, port=s.consul_port, token=s.consul_token)
        consul_client.agent.service.register.assert_called_once_with(self.service_name,
                                                                     service_id=ANY,
                                                                     port=s.advertise_port,
                                                                     address=s.advertise_address,
                                                                     check=ANY,
                                                                     tags=[UUID, self.service_name])

    @patch('xivo.consul_helpers.Consul')
    def test_that_register_raises_if_register_fails(self, Consul):
        consul_client = Consul.return_value
        consul_client.agent.service.register.return_value = False

        self.assertRaises(RegistererError, self.registerer.register)

        consul_client.agent.service.register.assert_called_once_with(self.service_name,
                                                                     service_id=ANY,
                                                                     port=s.advertise_port,
                                                                     address=s.advertise_address,
                                                                     check=ANY,
                                                                     tags=[UUID, self.service_name])

    @patch('xivo.consul_helpers.Consul')
    def test_that_deregister_calls_agent_deregister_service_and_check(self, Consul):
        consul_client = Consul.return_value

        self.registerer.deregister()

        Consul.assert_called_once_with(host=s.consul_host, port=s.consul_port, token=s.consul_token)
        consul_client.agent.service.deregister.assert_called_with(self.registerer._service_id)
        consul_client.agent.check.deregister.assert_called_with(self.registerer._check_id)
