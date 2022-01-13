# Copyright 2016-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import kombu
import threading
import requests

from consul import Consul
from contextlib import contextmanager
from hamcrest import assert_that, contains_inanyorder, contains_string, equal_to
from six.moves import queue
from kombu.mixins import ConsumerMixin
from wazo_test_helpers import until
from wazo_test_helpers.asset_launching_test_case import (
    AssetLaunchingTestCase,
    _run_cmd,
    NoSuchService,
)

ASSET_ROOT = os.path.join(os.path.dirname(__file__), '..', 'assets')
BUS_URL = 'amqp://{username}:{password}@{host}:{port}//'


class ServiceConsumer(ConsumerMixin):

    _exchange = kombu.Exchange('xivo', type='topic')
    _routing_key = 'service.#'

    def __init__(self, connection, message_queue):
        self.connection = connection
        self._queue = kombu.Queue(
            exchange=self._exchange, routing_key=self._routing_key
        )
        self._received_messages = message_queue
        self._is_running = False

    def get_consumers(self, Consumer, channel):
        return [Consumer(self._queue, callbacks=[self.on_message])]

    def on_connection_error(self, exc, interval):
        super(ServiceConsumer, self).on_connection_error(exc, interval)
        self._is_running = False

    def on_connection_revived(self):
        super(ServiceConsumer, self).on_connection_revived()
        self._is_running = True

    def on_message(self, body, message):
        self._received_messages.put_nowait(body)
        message.ack()

    def get_message(self):
        return self._received_messages.get()

    def is_running(self):
        return self._is_running


class _BaseTest(AssetLaunchingTestCase):

    assets_root = ASSET_ROOT
    service = 'myservice'

    @contextmanager
    def myservice(self, ip=None, enabled=True):
        self._run_docker_compose_cmd(['stop', self.service])
        self._run_docker_compose_cmd(['rm', '-f', self.service])

        if not enabled:
            self._run_docker_compose_cmd(
                ['run', '-d', '-e', 'DISABLED=1', self.service]
            )
        elif not ip:
            self._run_docker_compose_cmd(['run', '-d', self.service])
        else:
            self._run_docker_compose_cmd(
                ['run', '-d', '-e', 'ADVERTISE_ADDR={}'.format(ip), self.service]
            )

        status = self.service_status('myservice')

        try:
            network_name = '{}_default'.format(self.service)
            yield ip or status['NetworkSettings']['Networks'][network_name]['IPAddress']
        finally:
            id_ = status['Id']
            self._run_cmd('docker stop --time 20 {}'.format(id_))

    def _run_docker_compose_cmd(self, cmd):
        self._run_cmd(
            'docker-compose {} {}'.format(
                ' '.join(self._docker_compose_options()), ' '.join(cmd)
            )
        )

    # NOTE(fblackburn): override to include containers started with run command
    @classmethod
    def _container_id(cls, service_name):
        specific_options = ['-a', '--status', 'running']
        result = _run_cmd(
            ['docker-compose']
            + cls._docker_compose_options()
            + ['ps', '-q']
            + specific_options
            + [service_name],
            stderr=False,
        ).stdout.strip()
        result = result.decode('utf-8')
        if '\n' in result:
            raise AssertionError(
                f'There is more than one container running with name {service_name}'
            )
        if not result:
            raise NoSuchService(service_name)
        return result


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
            assert_that(
                self.service_logs(),
                contains_string('service discovery has been disabled'),
            )

        with self.myservice(enabled=False) as ip:
            until.assert_(logs_says_disabled, tries=10)


class TestServiceDiscovery(_BaseTest):

    asset = 'service_discovery'

    def setUp(self):
        self._consumer = None
        self.messages = queue.Queue()
        self.start_listening()

    def start_listening(self):
        self._bus_thread = threading.Thread(target=self._start_consuming)
        self._bus_thread.start()

        def is_listening():
            return self._consumer and self._consumer.is_running()

        until.true(is_listening, tries=20, interval=0.5)

    def _start_consuming(self):
        bus_url = BUS_URL.format(
            username='guest',
            password='guest',
            host='127.0.0.1',
            port=self.service_port(5672, 'rabbitmq'),
        )
        with kombu.Connection(bus_url) as conn:
            conn.ensure_connection()
            self._consumer = ServiceConsumer(conn, self.messages)
            self._consumer.run()

    def tearDown(self):
        self.stop_listening()

    def stop_listening(self):
        self._consumer.should_stop = True
        self._bus_thread.join()
        self._consumer = None

    def empty_message_queue(self):
        while not self.messages.empty():
            print('removing', self.messages.get_nowait())

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
        with self.myservice() as ip:
            self.assert_registered_msg_received(
                ip
            )  # to remove the message from the queue
            self.stop_listening()
            self._run_cmd('docker-compose restart rabbitmq')
            self.start_listening()
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
        port = self.service_port(8500, 'consul')
        consul = Consul('127.0.0.1', port, 'the_one_ring')
        services = consul.agent.services()
        for index, service in services.items():
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
        except queue.Empty:
            self.fail('Should have received a message')
