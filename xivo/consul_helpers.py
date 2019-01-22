# -*- coding: utf-8 -*-
# Copyright 2015-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import logging
import threading
import socket

from uuid import uuid4
import requests

from consul import Check, Consul, ConsulException
from requests.exceptions import ConnectionError

try:
    from kombu import Connection, Exchange, Producer
except ImportError:
    pass

try:
    import netifaces
except ImportError:
    pass

try:
    from xivo_bus.resources.services import event
    from xivo_bus import Publisher, Marshaler
except ImportError:
    pass


logger = logging.getLogger('service_discovery')
VALID_SERVICE_DISCO_IFACE_PREFIX = ['eth', 'en']


class RegistererError(Exception):
    pass


class ServiceDiscoveryError(Exception):
    pass


class MissingConfigurationError(RegistererError):
    pass


class ServiceCatalogRegistration(object):

    def __init__(self, service_name, uuid, consul_config,
                 service_discovery_config, bus_config, check=None):
        self._enabled = service_discovery_config.get('enabled', True)
        if not self._enabled:
            logger.debug('service discovery has been disabled')
            return

        self._check = check or self._default_check
        self._registerer = NotifyingRegisterer(service_name, uuid, consul_config,
                                               service_discovery_config, bus_config)

        self._retry_interval = service_discovery_config['retry_interval']
        self._refresh_interval = service_discovery_config['refresh_interval']

        self._thread = threading.Thread(target=self._loop)
        self._sleep_event = threading.Event()
        self._thread.daemon = True
        self._thread.name = 'ServiceDiscoveryThread'

        self._done = False
        self._registered = False

    def __enter__(self):
        if self._enabled:
            self._thread.start()
        return self

    def __exit__(self, type, value, traceback):
        if type:
            logger.debug('An error occured: %s %s %s', type, value, traceback)

        if not self._enabled:
            return

        if self._thread.is_alive():
            logger.debug('waiting for the service discovery thread to complete')
            self._done = True
            self._wake()
            self._thread.join()

        try:
            self._registerer.deregister()
        except RegistererError as e:
            logger.info('failed to deregister %s', e)
        except Exception:
            logger.exception('failed to deregister')

    def _loop(self):
        while not self._done:
            if not self._registered:
                service_ready = self._check()
                if service_ready:
                    self._register()

            if self._registered and self._registerer.send_ttl():
                self._sleep(self._refresh_interval)
            else:
                self._sleep(self._retry_interval)

    def _sleep(self, interval):
        self._sleep_event.wait(interval)

    def _wake(self):
        self._sleep_event.set()

    def _register(self):
        try:
            self._registerer.register()
            self._registered = True
        except RegistererError as e:
            logger.info('registration failed, retrying in %s seconds %s', self._retry_interval, e)

    def _default_check(self):
        return True


class Registerer(object):

    def __init__(self, name, uuid, consul_config, service_discovery_config):
        self._service_id = str(uuid4())
        self._service_name = name
        try:
            self._advertise_address = self._find_address(service_discovery_config)
            self._advertise_port = service_discovery_config['advertise_port']
            self._tags = [uuid, name] + service_discovery_config.get('extra_tags', [])

            self._ttl_interval = '{}s'.format(service_discovery_config['ttl_interval'])
        except KeyError as e:
            raise MissingConfigurationError(str(e))
        self._consul_config = consul_config
        self._check_id = 'service:{}'.format(self._service_id)

    @property
    def _client(self):
        return Consul(**self._consul_config)

    def register(self):
        logger.info('Registering %s on Consul as %s with %s:%s',
                    self._service_name,
                    self._service_id,
                    self._advertise_address,
                    self._advertise_port)

        try:
            ttl_check = Check.ttl(self._ttl_interval)
            registered = self._client.agent.service.register(self._service_name,
                                                             service_id=self._service_id,
                                                             address=self._advertise_address,
                                                             port=self._advertise_port,
                                                             check=ttl_check,
                                                             tags=self._tags)
            if not registered:
                raise RegistererError('{} registration on Consul failed'.format(self._service_name))

        except (ConnectionError, ConsulException) as e:
            raise RegistererError(str(e))

    def send_ttl(self):
        result = None

        try:
            result = self._client.agent.check.ttl_pass(self._check_id)
        except ConnectionError as e:
            logger.info('%s', e)

        if not result:
            logger.info('ttl pass failed')

        return result

    def deregister(self):
        logger.info('Deregistering %s from Consul services: %s',
                    self._service_name,
                    self._service_id)

        try:
            client = self._client
            client.agent.check.deregister(self._check_id)
            return client.agent.service.deregister(self._service_id)
        except (ConnectionError, ConsulException) as e:
            raise RegistererError(str(e))

    def _find_address(self, service_discovery_config):
        return address_from_config(service_discovery_config)


def address_from_config(service_discovery_config):
    advertise_address = service_discovery_config['advertise_address']
    if advertise_address != 'auto':
        return advertise_address

    return _find_address(service_discovery_config['advertise_address_interface'])


def _find_address(main_iface):
    def _is_valid_iface_name(name):
        for prefix in VALID_SERVICE_DISCO_IFACE_PREFIX:
            if name.startswith(prefix):
                return True
        return False

    ifaces = [main_iface] + [iface for iface in netifaces.interfaces() if _is_valid_iface_name(iface)] + ['lo']
    for iface in ifaces:
        try:
            for config in netifaces.ifaddresses(iface).get(netifaces.AF_INET, []):
                address = config.get('addr')
                if address:
                    return address
        except ValueError:
            logger.info('The configured interface does not exists: %s', iface)

    return '127.0.0.1'


class NotifyingRegisterer(Registerer):

    bus_uri_pattern = 'amqp://{username}:{password}@{host}:{port}//'

    def __init__(self, name, uuid, consul_config, service_discovery_config, bus_config):
        super(NotifyingRegisterer, self).__init__(name, uuid, consul_config, service_discovery_config)
        self._bus_config = bus_config
        self._marshaler = Marshaler(uuid)
        try:
            self._bus_url = bus_config.get('uri') or self.bus_uri_pattern.format(**bus_config)
        except KeyError as e:
            raise MissingConfigurationError(str(e))

    def register(self):
        super(NotifyingRegisterer, self).register()
        msg = self._new_registered_event()
        self._send_msg(msg)

    def deregister(self):
        exception = None
        try:
            should_send_msg = super(NotifyingRegisterer, self).deregister()
        except RegistererError as e:
            should_send_msg = True
            exception = e

        if should_send_msg:
            msg = self._new_deregistered_event()
            self._send_msg(msg)

        if exception:
            raise exception

        return should_send_msg

    def _send_msg(self, msg):
        try:
            with Connection(self._bus_url) as conn:
                exchange = Exchange(self._bus_config['exchange_name'],
                                    self._bus_config['exchange_type'])
                producer = Producer(conn, exchange=exchange, auto_declare=True)
                publisher = Publisher(producer, self._marshaler)
                publisher.publish(msg)
        except socket.error:
            raise RegistererError('failed to publish on rabbitmq')

    def _new_deregistered_event(self):
        return event.ServiceDeregisteredEvent(self._service_name,
                                              self._service_id,
                                              self._tags)

    def _new_registered_event(self):
        return event.ServiceRegisteredEvent(self._service_name,
                                            self._service_id,
                                            self._advertise_address,
                                            self._advertise_port,
                                            self._tags)


class ServiceFinder(object):

    def __init__(self, consul_config):
        self._dc_url = '{scheme}://{host}:{port}/v1/catalog/datacenters'.format(**consul_config)
        self._health_url = '{scheme}://{host}:{port}/v1/health/service'.format(**consul_config)
        self._service_url = '{scheme}://{host}:{port}/v1/catalog/service'.format(**consul_config)
        self._verify = consul_config.get('verify', True)
        self._token = consul_config.get('token')

    def list_healthy_services(self, service_name, xivo_uuid=None):
        services = []
        for dc in self._get_datacenters():
            for service in self._list_running_services(service_name, dc, tag=xivo_uuid):
                services.append(service)
        return services

    def _get_datacenters(self):
        response = requests.get(self._dc_url,
                                verify=self._verify)
        self._assert_ok(response)
        return response.json()

    def _list_running_services(self, service_name, datacenter, tag):
        url = '{}/{}'.format(self._health_url, service_name)
        params = {'dc': datacenter, 'passing': True}
        if tag:
            params['tag'] = tag
        response = requests.get(url, verify=self._verify, params=params)
        self._assert_ok(response)
        services = []
        for node in response.json():
            service = node.get('Service')
            if service:
                services.append(service)
        return services

    @staticmethod
    def _assert_ok(response, code=200):
        if response.status_code != code:
            msg = getattr(response, 'text', 'unknown error')
            raise ServiceDiscoveryError(msg)
