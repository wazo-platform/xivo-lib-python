# -*- coding: utf-8 -*-
# Copyright 2015-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
import uuid

from hamcrest import assert_that, calling, contains, equal_to, raises
from mock import ANY, call, patch, Mock, sentinel as s
from xivo_bus.resources.services import event


from ..consul_helpers import (
    NotifyingRegisterer,
    Registerer,
    RegistererError,
    ServiceFinder,
    ServiceDiscoveryError,
    _find_address,
)


UUID = str(uuid.uuid4())
BUS_CONFIG = {
    'username': 'bus_username',
    'password': 'bus_password',
    'host': 'localhost',
    'port': 5532,
    'exchange_name': 'xchange',
    'exchange_type': 'topic',
}


class TestFindIpAddress(unittest.TestCase):
    def test_that_the_main_iface_is_used_if_it_has_an_ip_address(self):
        with patch('xivo.consul_helpers.netifaces') as netifaces:
            netifaces.interfaces.return_value = ['lo', 'eth0', 'eth1', 'eth3']
            netifaces.ifaddresses.return_value = {
                netifaces.AF_INET: [{'addr': s.eth3_ip}]
            }

            result = _find_address('eth3')

            self._assert_called(netifaces.ifaddresses, 'eth3')

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

            self._assert_called(netifaces.ifaddresses, 'eth3', 'eth0', 'eth1')

        assert_that(result, equal_to(s.eth1_ip))

    def test_that_en_ifaces_are_used_in_order_if_the_first_has_no_address(self):
        def return_values(iface):
            if iface == 'enp0s1':
                return {netifaces.AF_INET: [{'addr': s.enp0s1}]}
            elif iface == 'enp0s3':
                return {netifaces.AF_INET: [{'broadcast': '255.255.255.0'}]}
            else:
                return {}

        with patch('xivo.consul_helpers.netifaces') as netifaces:
            netifaces.interfaces.return_value = ['lo', 'ens1', 'eno3', 'enp0s1']
            netifaces.ifaddresses.side_effect = return_values

            result = _find_address('enp0s3')

            self._assert_called(
                netifaces.ifaddresses, 'enp0s3', 'ens1', 'eno3', 'enp0s1'
            )

        assert_that(result, equal_to(s.enp0s1))

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

            self._assert_called(
                netifaces.ifaddresses, 'eth3', 'eth0', 'eth1', 'eth2', 'eth3', 'lo'
            )

        assert_that(result, equal_to(s.lo_ip))

    def test_that_127001_is_returned_if_all_else_fails(self):
        with patch('xivo.consul_helpers.netifaces') as netifaces:
            netifaces.interfaces.return_value = ['lo', 'eth0', 'eth1']
            netifaces.ifaddresses.return_value = {}

            result = _find_address('eth3')

            self._assert_called(netifaces.ifaddresses, 'eth3', 'eth0', 'eth1', 'lo')

        assert_that(result, equal_to('127.0.0.1'))

    def test_that_an_invalid_iface_does_not_raise(self):
        with patch('xivo.consul_helpers.netifaces') as netifaces:
            netifaces.interfaces.return_value = ['lo', 'eth0', 'eth1']
            netifaces.ifaddresses.side_effect = ValueError

            result = _find_address('eth3')

            self._assert_called(netifaces.ifaddresses, 'eth3', 'eth0', 'eth1', 'lo')

        assert_that(result, equal_to('127.0.0.1'))

    def _assert_called(self, mock, *args):
        expected_calls = [call(arg) for arg in args]
        mock.assert_has_calls(expected_calls)


class TestNotifyingRegisterer(unittest.TestCase):
    def setUp(self):
        self.service_name = 'foobar'
        consul_config = {
            'host': s.consul_host,
            'port': s.consul_port,
            'token': s.consul_token,
        }
        service_discovery_config = {
            'advertise_port': 4242,
            'advertise_address': 'localhost',
            'ttl_interval': 10,
            'extra_tags': [],
        }
        self.registerer = NotifyingRegisterer(
            self.service_name, UUID, consul_config, service_discovery_config, BUS_CONFIG
        )
        self.service_id = self.registerer._service_id

    @patch('xivo.consul_helpers.Consul', Mock())
    def test_that_register_sends_a_service_registered_event_when_registered(self):
        with patch.object(self.registerer, '_send_msg') as send_msg:
            self.registerer.register()

            expected_message = event.ServiceRegisteredEvent(
                self.service_name,
                self.service_id,
                'localhost',
                4242,
                [UUID, self.service_name],
            )

            send_msg.assert_called_once_with(expected_message)

    @patch('xivo.consul_helpers.Consul')
    def test_that_deregister_sends_a_service_deregistered_event_when_registered(
        self, Consul
    ):
        consul_client = Consul.return_value
        consul_client.agent.service.deregister.return_value = True

        with patch.object(self.registerer, '_send_msg') as send_msg:
            self.registerer.deregister()

        expected_message = event.ServiceDeregisteredEvent(
            self.service_name, self.service_id, [UUID, self.service_name]
        )

        send_msg.assert_called_once_with(expected_message)

    @patch('xivo.consul_helpers.Consul')
    def test_that_deregister_sends_a_service_deregistered_event_when_not_registered(
        self, Consul
    ):
        consul_client = Consul.return_value
        consul_client.agent.service.deregister.return_value = False

        with patch.object(self.registerer, '_send_msg') as send_msg:
            self.registerer.deregister()
            assert_that(send_msg.call_count, equal_to(0))


class TestConsulRegisterer(unittest.TestCase):
    def setUp(self):
        self.service_name = 'my-service'
        consul_config = {
            'host': s.consul_host,
            'port': s.consul_port,
            'token': s.consul_token,
        }
        service_discovery_config = {
            'advertise_address': s.advertise_address,
            'advertise_port': s.advertise_port,
            'ttl_interval': 10,
            'extra_tags': [],
        }
        self.registerer = Registerer(
            self.service_name, UUID, consul_config, service_discovery_config
        )

    @patch('xivo.consul_helpers.Consul')
    def test_that_register_calls_agent_register(self, Consul):
        consul_client = Consul.return_value

        self.registerer.register()

        Consul.assert_called_once_with(
            host=s.consul_host, port=s.consul_port, token=s.consul_token
        )
        consul_client.agent.service.register.assert_called_once_with(
            self.service_name,
            service_id=ANY,
            port=s.advertise_port,
            address=s.advertise_address,
            check=ANY,
            tags=[UUID, self.service_name],
        )

    @patch('xivo.consul_helpers.Consul')
    def test_that_register_raises_if_register_fails(self, Consul):
        consul_client = Consul.return_value
        consul_client.agent.service.register.return_value = False

        self.assertRaises(RegistererError, self.registerer.register)

        consul_client.agent.service.register.assert_called_once_with(
            self.service_name,
            service_id=ANY,
            port=s.advertise_port,
            address=s.advertise_address,
            check=ANY,
            tags=[UUID, self.service_name],
        )

    @patch('xivo.consul_helpers.Consul')
    def test_that_deregister_calls_agent_deregister_service_and_check(self, Consul):
        consul_client = Consul.return_value

        self.registerer.deregister()

        Consul.assert_called_once_with(
            host=s.consul_host, port=s.consul_port, token=s.consul_token
        )
        consul_client.agent.service.deregister.assert_called_with(
            self.registerer._service_id
        )
        consul_client.agent.check.deregister.assert_called_with(
            self.registerer._check_id
        )


class BaseFinderTestCase(unittest.TestCase):
    def setUp(self):
        self.consul_config = {
            'token': 'master-token',
            'scheme': 'http',
            'port': 8500,
            'host': 'localhost',
            'verify': True,
        }


@patch('xivo.consul_helpers.requests')
class TestRemoteServiceFinderGetDatacenters(BaseFinderTestCase):
    def test_that_the_url_matches_the_config(self, requests):
        requests.get.return_value = Mock(status_code=200)
        url_and_configs = [
            ('http://localhost:8500/v1/catalog/datacenters', self.consul_config),
            (
                'https://192.168.1.1:2155/v1/catalog/datacenters',
                {'scheme': 'https', 'host': '192.168.1.1', 'port': 2155},
            ),
        ]

        for url, config in url_and_configs:
            finder = ServiceFinder(config)
            finder._get_datacenters()
            requests.get.assert_called_once_with(url, verify=ANY)
            requests.reset_mock()

    def test_that_raises_if_not_200(self, requests):
        requests.get.return_value = Mock(status_code=403, text='some error')

        finder = ServiceFinder(self.consul_config)

        assert_that(calling(finder._get_datacenters), raises(ServiceDiscoveryError))

    def test_that_health_uses_the_configured_verify(self, requests):
        requests.get.return_value = Mock(status_code=200)
        verify_and_configs = [
            (True, self.consul_config),
            (
                False,
                {
                    'verify': False,
                    'scheme': 'https',
                    'host': '192.168.1.1',
                    'port': 2155,
                },
            ),
        ]

        for verify, config in verify_and_configs:
            finder = ServiceFinder(config)
            finder._get_datacenters()
            requests.get.assert_called_once_with(ANY, verify=verify)
            requests.reset_mock()


@patch('xivo.consul_helpers.requests')
class TestRemoteServiceFinderListRunningServices(BaseFinderTestCase):
    def test_that_the_health_url_matches_the_config(self, requests):
        requests.get.return_value = Mock(status_code=200, json=Mock(return_value=[]))
        url_and_configs = [
            ('http://localhost:8500/v1/health/service/foobar', self.consul_config),
            (
                'https://192.168.1.1:2155/v1/health/service/foobar',
                {'scheme': 'https', 'host': '192.168.1.1', 'port': 2155},
            ),
        ]

        for url, config in url_and_configs:
            finder = ServiceFinder(config)
            finder._list_running_services('foobar', s.dc, None)
            requests.get.assert_called_once_with(url, verify=ANY, params=ANY)
            requests.reset_mock()

    def test_that_the_verify_config_is_user(self, requests):
        requests.get.return_value = Mock(status_code=200, json=Mock(return_value=[]))
        verify_and_configs = [
            (True, self.consul_config),
            (
                False,
                {
                    'verify': False,
                    'scheme': 'https',
                    'host': '192.168.1.1',
                    'port': 2155,
                },
            ),
        ]

        for verify, config in verify_and_configs:
            finder = ServiceFinder(config)
            finder._list_running_services('foobar', s.dc, None)
            requests.get.assert_called_once_with(ANY, verify=verify, params=ANY)
            requests.reset_mock()

    def test_that_params_are_based_on_the_datacenter(self, requests):
        requests.get.return_value = Mock(status_code=200, json=Mock(return_value=[]))

        finder = ServiceFinder(self.consul_config)

        for dc in ['dc1', 'dc2']:
            finder._list_running_services('foobar', dc, None)
            expected = {'dc': dc, 'passing': True}
            requests.get.assert_called_once_with(ANY, verify=ANY, params=expected)
            requests.reset_mock()

    def test_that_param_contains_the_optionnal_tag(self, requests):
        requests.get.return_value = Mock(status_code=200, json=Mock(return_value=[]))

        finder = ServiceFinder(self.consul_config)

        finder._list_running_services('foobar', s.db, tag=s.tag)
        expected = {'dc': s.db, 'passing': True, 'tag': s.tag}
        requests.get.assert_called_once_with(ANY, verify=ANY, params=expected)

    def test_that_raises_if_not_200(self, requests):
        requests.get.return_value = Mock(status_code=403, text='some error')

        finder = ServiceFinder(self.consul_config)

        assert_that(
            calling(finder._list_running_services).with_args('foobar', 'dc1', None),
            raises(Exception),
        )

    def test_that_returns_services_from_each_nodes(self, requests):
        node_0_service = {
            "ID": "1c8c13d8-adca-4715-8bf3-04e51509f141",
            "Service": "wazo-calld",
            "Tags": ["f9f0f3bb-f577-4354-9109-9cf6cf7c7adf", "wazo-calld"],
            "Port": 9495,
            "Address": "10.37.0.254",
            "EnableTagOverride": False,
        }
        node_1_service = {
            "ID": "1c8c13d8-adca-4715-b1b1-04e51509f141",
            "Service": "wazo-calld",
            "Tags": ["f9f0f3bb-f577-4354-b1b1-9cf6cf7c7adf", "wazo-calld"],
            "Port": 9495,
            "Address": "10.37.1.254",
            "EnableTagOverride": False,
        }

        response = [
            {
                "Node": {"Node": "pcm-dev-0", "Address": "10.37.0.254"},
                "Service": node_0_service,
                "Checks": [],
            },
            {
                "Node": {"Node": "pcm-dev-1", "Address": "10.37.1.254"},
                "Service": node_1_service,
                "Checks": [],
            },
        ]
        requests.get.return_value = Mock(
            status_code=200, json=Mock(return_value=response)
        )

        finder = ServiceFinder(self.consul_config)
        result = finder._list_running_services('wazo-calld', 'dc1', None)

        assert_that(result, contains(node_0_service, node_1_service))
