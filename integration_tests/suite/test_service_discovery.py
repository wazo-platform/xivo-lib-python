# -*- coding: utf-8 -*-
# Copyright (C) 2016 Avencall
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

import os
import kombu
import threading
import requests

from consul import Consul
from contextlib import contextmanager
from hamcrest import assert_that, contains_inanyorder, contains_string, equal_to
from Queue import Empty, Queue
from kombu.mixins import ConsumerMixin
from xivo_test_helpers import until
from xivo_test_helpers.asset_launching_test_case import AssetLaunchingTestCase

ASSET_ROOT = os.path.join(os.path.dirname(__file__), '..', 'assets')


class ServiceConsumer(ConsumerMixin):

    _exchange = kombu.Exchange('xivo', type='topic')
    _routing_key = 'service.#'

    def __init__(self, connection, message_queue):
        self.connection = connection
        self._queue = kombu.Queue(exchange=self._exchange, routing_key=self._routing_key)
        self._received_messages = message_queue

    def get_consumers(self, Consumer, channel):
        return [Consumer(self._queue, callbacks=[self.on_message])]

    def on_message(self, body, message):
        self._received_messages.put_nowait(body)
        message.ack()

    def get_message(self):
        return self._received_messages.get()


class _BaseTest(AssetLaunchingTestCase):

    assets_root = ASSET_ROOT
    service = 'myservice'

    @contextmanager
    def myservice(self, ip=None, enabled=True):
        self._run_cmd('docker-compose stop myservice')
        self._run_cmd('docker-compose rm -f myservice')

        if not enabled:
            self._run_cmd('docker-compose run -d -e DISABLED=1 myservice')
        elif not ip:
            self._run_cmd('docker-compose run -d myservice')
        else:
            self._run_cmd('docker-compose run -d -e ADVERTISE_ADDR={} myservice'.format(ip))
        status = self.service_status('myservice')

        try:
            yield ip or status['NetworkSettings']['IPAddress']
        finally:
            id_ = status['Id']
            self._run_cmd('docker stop {}'.format(id_))


class TestServiceDiscoveryDisabled(_BaseTest):

    asset = 'service_discovery_disabled'

    def test_that_my_service_can_start_when_service_disc_is_disabled(self):

        def logs_says_disabled():
            url = 'http://{}:{}/0.1/infos'.format(ip, 6262)
            try:
                r = requests.get(url)
            except Exception:
                raise AssertionError('service is not available')
            assert_that(r.status_code, equal_to(200))
            assert_that(self.service_logs(), contains_string('service discovery has been disabled'))

        with self.myservice(enabled=False) as ip:
            until.assert_(logs_says_disabled, tries=10)


class TestServiceDiscovery(_BaseTest):

    assets_root = ASSET_ROOT
    asset = 'service_discovery'
    bus_url = 'amqp://{username}:{password}@{host}:{port}//'.format(username='guest',
                                                                    password='guest',
                                                                    host='localhost',
                                                                    port=5672)

    def setUp(self):
        self.messages = Queue()
        self._bus_thread = threading.Thread(target=self._start_consuming)
        self._bus_thread.start()

    def _start_consuming(self):
        with kombu.Connection(self.bus_url) as conn:
            self._consumer = ServiceConsumer(conn, self.messages)
            self._consumer.run()

    def tearDown(self):
        self._consumer.should_stop = True
        self._bus_thread.join()

    def empty_message_queue(self):
        while not self.messages.empty():
            print 'removing', self.messages.get_nowait()

    def test_that_the_bus_message_is_received_on_start_and_stop_with_auth(self):
        with self.myservice() as ip:
            self.assert_registered_msg_received(ip)
            self.empty_message_queue()
        self.assert_deregistered_msg_received()

    def test_that_the_catalog_is_updated_on_start_and_stop_with_auth(self):
        with self.myservice() as ip:
            self._wait_for_registered_message(10)
            self.assert_registered_on_the_catalog(ip)
        self.assert_deregistered_from_the_catalog(ip)

    def test_that_the_bus_message_is_received_on_start_and_stop_with_address(self):
        with self.myservice('169.0.0.1') as ip:
            self.assert_registered_msg_received(ip)
            self.empty_message_queue()
        self.assert_deregistered_msg_received()

    def test_that_the_catalog_is_updated_on_start_and_stop_with_address(self):
        address = '169.0.0.1'
        with self.myservice(address):
            self._wait_for_registered_message(10)
            self.assert_registered_on_the_catalog(address)
        self.assert_deregistered_from_the_catalog(address)

    def test_that_the_bus_message_is_received_on_stop_when_rabbitmq_is_restarted(self):
        with self.myservice():
            _run_cmd('docker-compose restart rabbitmq')
            self.empty_message_queue()
        self.assert_deregistered_msg_received()

    def _wait_for_registered_message(self, timeout):
        self.messages.get(timeout=timeout)

    def assert_registered_on_the_catalog(self, ip):
        registered = self._is_myservice_registered_to_consul(ip)
        assert_that(registered, equal_to(True))

    def assert_deregistered_from_the_catalog(self, ip):
        registered = self._is_myservice_registered_to_consul(ip)
        assert_that(registered, equal_to(False))

    def _is_myservice_registered_to_consul(self, ip):
        consul = Consul('localhost', '8500', 'the_one_ring')
        services = consul.agent.services()
        for index, service in services.iteritems():
            if service['Service'] == 'myservice' and service['Address'] == ip:
                return True

        return False

    def assert_deregistered_msg_received(self):
        message = self._get_message()
        assert_that(message['name'], equal_to('service_deregistered_event'))
        assert_that(message['origin_uuid'], equal_to('foobar'))
        assert_that(message['data']['service_name'], equal_to('myservice'))
        assert_that(message['data']['tags'], contains_inanyorder('foobar', 'myservice'))

    def assert_registered_msg_received(self, ip):
        message = self._get_message()
        assert_that(message['name'], equal_to('service_registered_event'))
        assert_that(message['origin_uuid'], equal_to('foobar'))
        assert_that(message['data']['service_name'], equal_to('myservice'))
        assert_that(message['data']['address'], equal_to(ip))
        assert_that(message['data']['port'], equal_to(6262))
        assert_that(message['data']['tags'], contains_inanyorder('foobar', 'myservice'))

    def _get_message(self):
        try:
            return self.messages.get(timeout=30)
        except Empty:
            self.fail('Should have received a message')
