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

from hamcrest import assert_that, contains, equal_to
from mock import ANY, call, patch, Mock, sentinel as s
from xivo_bus.resources.services import event


from ..consul_helpers import (NotifyingRegisterer,
                              Registerer,
                              RegistererError,
                              _find_address)


UUID = str(uuid.uuid4())
BUS_CONFIG = {'username': 'bus_username',
              'password': 'bus_password',
              'host': 'localhost',
              'port': 5532,
              'exchange_name': 'xchange',
              'exchange_type': 'topic'}


class TestFindIpAddress(unittest.TestCase):

    def test_that_the_main_iface_is_used_if_it_has_an_ip_address(self):
        with patch('xivo.consul_helpers.netifaces') as netifaces:
            netifaces.interfaces.return_value = ['lo', 'eth0', 'eth1', 'eth3']
            netifaces.ifaddresses.return_value = {netifaces.AF_INET: [{'addr': s.eth3_ip}]}

            result = _find_address('eth3')

            netifaces.ifaddresses.assert_called_once_with('eth3')

        assert_that(result, equal_to(s.eth3_ip))

    def test_that_eth_ifaces_are_used_in_order_if_the_first_has_no_address(self):
        def return_values(iface):
            if iface == 'eth1':
                return {netifaces.AF_INET: [{'addr': s.eth1_ip}]}
            elif iface == 'eth3':
                return {}
            elif iface == 'eth0':
                return {netifaces.AF_INET: [{'broadcast': '255.255.255.0'}]}

        with patch('xivo.consul_helpers.netifaces') as netifaces:
            netifaces.interfaces.return_value = ['lo', 'eth0', 'eth1', 'eth3']
            netifaces.ifaddresses.side_effect = return_values

            result = _find_address('eth3')

            assert_that(netifaces.ifaddresses.mock_calls, contains(call('eth3'), call('eth0'), call('eth1')))

        assert_that(result, equal_to(s.eth1_ip))

    def test_that_lo_is_used_when_no_address_is_found_on_other_ifaces(self):
        def return_values(iface):
            if iface == 'lo':
                return {netifaces.AF_INET: [{'addr': s.lo_ip}]}
            else:
                return {}

        with patch('xivo.consul_helpers.netifaces') as netifaces:
            netifaces.interfaces.return_value = ['lo', 'eth0', 'eth1', 'eth2', 'eth3']
            netifaces.ifaddresses.side_effect = return_values

            result = _find_address('eth3')

            assert_that(netifaces.ifaddresses.mock_calls, contains(call('eth3'),
                                                                   call('eth0'),
                                                                   call('eth1'),
                                                                   call('eth2'),
                                                                   call('eth3'),
                                                                   call('lo')))

        assert_that(result, equal_to(s.lo_ip))

    def test_that_127001_us_returned_if_all_else_fails(self):
        with patch('xivo.consul_helpers.netifaces') as netifaces:
            netifaces.interfaces.return_value = ['lo', 'eth0', 'eth1']
            netifaces.ifaddresses.return_value = {}

            result = _find_address('eth3')

            assert_that(netifaces.ifaddresses.mock_calls, contains(call('eth3'),
                                                                   call('eth0'),
                                                                   call('eth1'),
                                                                   call('lo')))

        assert_that(result, equal_to('127.0.0.1'))

    def test_that_an_invalid_iface_does_not_raise(self):
        with patch('xivo.consul_helpers.netifaces') as netifaces:
            netifaces.interfaces.return_value = ['lo', 'eth0', 'eth1']
            netifaces.ifaddresses.side_effect = ValueError

            result = _find_address('eth3')

            assert_that(netifaces.ifaddresses.mock_calls, contains(call('eth3'),
                                                                   call('eth0'),
                                                                   call('eth1'),
                                                                   call('lo')))

        assert_that(result, equal_to('127.0.0.1'))


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
