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

from hamcrest import assert_that, contains_inanyorder, equal_to
from mock import ANY, patch, Mock, sentinel as s
from xivo_bus import Publisher
from xivo_bus.resources.services import event


from ..consul_helpers import MissingConfigurationError, NotifyingRegisterer, Registerer, RegistererError


class TestNotifyingRegisterer(unittest.TestCase):

    def setUp(self):
        self.publisher = Mock(Publisher)
        self.service_name = 'foobar'
        consul_config = {'host': s.consul_host,
                         'port': s.consul_port,
                         'token': s.consul_token}
        self.registerer = NotifyingRegisterer(name=self.service_name,
                                              publisher=self.publisher,
                                              consul_config=consul_config,
                                              advertise_address=s.advertise_address,
                                              advertise_port=s.advertise_port,
                                              check_url=s.check_url,
                                              check_url_timeout=s.check_url_timeout,
                                              check_url_interval=s.check_url_interval,
                                              service_tags=[s.uuid, s.service_name])
        self.service_id = self.registerer._service_id

    @patch('xivo.consul_helpers.Consul', Mock())
    def test_that_register_sends_a_service_registered_event_when_registered(self):
        self.registerer.register()

        expected_message = event.ServiceRegisteredEvent(self.service_name,
                                                        self.service_id,
                                                        s.advertise_address,
                                                        s.advertise_port,
                                                        [s.uuid, s.service_name])

        self.publisher.publish.assert_called_once_with(expected_message)

    @patch('xivo.consul_helpers.Consul')
    def test_that_deregister_sends_a_service_deregistered_event_when_registered(self, Consul):
        consul_client = Consul.return_value
        consul_client.agent.service.deregister.return_value = True

        self.registerer.deregister()

        expected_message = event.ServiceDeregisteredEvent(self.service_name,
                                                          self.service_id,
                                                          [s.uuid, s.service_name])

        self.publisher.publish.assert_called_once_with(expected_message)

    @patch('xivo.consul_helpers.Consul')
    def test_that_deregister_sends_a_service_deregistered_event_when_not_registered(self, Consul):
        consul_client = Consul.return_value
        consul_client.agent.service.deregister.return_value = False

        self.registerer.deregister()

        assert_that(self.publisher.publish.call_count, equal_to(0))


class TestConsulRegisterer(unittest.TestCase):

    def setUp(self):
        self.service_name = 'my-service'
        consul_config = {'host': s.consul_host,
                         'port': s.consul_port,
                         'token': s.consul_token}
        self.registerer = Registerer(name=self.service_name, consul_config=consul_config,
                                     advertise_address=s.advertise_address,
                                     advertise_port=s.advertise_port, check_url=s.check_url,
                                     check_url_timeout=s.check_url_timeout,
                                     check_url_interval=s.check_url_interval, service_tags=s.tags)

    @patch('xivo.consul_helpers.Consul')
    def test_that_register_calls_agent_register(self, Consul):
        consul_client = Consul.return_value

        self.registerer.register()

        Consul.assert_called_once_with(host=s.consul_host, port=s.consul_port, token=s.consul_token)
        consul_client.agent.service.register.assert_called_once_with(self.service_name,
                                                                     service_id=ANY,
                                                                     port=s.advertise_port,
                                                                     address=s.advertise_address,
                                                                     check=ANY, tags=s.tags)

    @patch('xivo.consul_helpers.Consul')
    def test_that_register_raises_if_register_fails(self, Consul):
        consul_client = Consul.return_value
        consul_client.agent.service.register.return_value = False

        self.assertRaises(RegistererError, self.registerer.register)

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

        Check.http.assert_called_once_with(s.check_url, s.check_url_interval, timeout=s.check_url_timeout)
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

        Consul.assert_called_once_with(host=s.consul_host, port=s.consul_port, token=s.consul_token)
        consul_client.agent.service.deregister.assert_called_once_with(self.registerer._service_id)


class TestFromConfigFactory(unittest.TestCase):

    def setUp(self):
        self.service_name = 'foobar'
        self.config = {'consul': {'host': s.consul_host,
                                  'port': s.consul_port,
                                  'token': s.consul_token},
                       'service_discovery': {'advertise_address': s.advertise_address,
                                             'advertise_port': s.advertise_port,
                                             'extra_tags': ['Paris'],
                                             'check_url': s.check_url,
                                             'check_url_timeout': s.check_url_timeout,
                                             'check_url_interval': s.check_url_interval},
                       'uuid': s.uuid}

    def test_registered_from_config(self):
        registerer = Registerer.from_config(self.service_name, self.config)

        self.assert_that_config_is_applied(registerer)

    def test_notifying_registered_from_config(self):
        registerer = NotifyingRegisterer.from_config(self.service_name, s.publisher, self.config)

        assert_that(registerer._publisher, equal_to(s.publisher))
        self.assert_that_config_is_applied(registerer)

    def test_from_config_missing_config(self):
        self.assertRaises(MissingConfigurationError, Registerer.from_config, 'foobar', {})

    def assert_that_config_is_applied(self, registerer):
        assert_that(registerer._service_name, equal_to(self.service_name))
        assert_that(registerer._advertise_address, equal_to(s.advertise_address))
        assert_that(registerer._advertise_port, equal_to(s.advertise_port))
        assert_that(registerer._tags, contains_inanyorder('Paris', self.service_name, s.uuid))
        assert_that(registerer._check_url, equal_to(s.check_url))
        assert_that(registerer._check_url_timeout, equal_to(s.check_url_timeout))
        assert_that(registerer._consul_config, equal_to({'host': s.consul_host,
                                                         'port': s.consul_port,
                                                         'token': s.consul_token}))
