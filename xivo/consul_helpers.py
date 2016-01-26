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

import logging
import threading
import uuid

from consul import Check, Consul, ConsulException
from requests.exceptions import ConnectionError

try:
    import netifaces
except ImportError:
    pass

try:
    from xivo_bus.resources.services import event
except ImportError:
    pass


logger = logging.getLogger('service_discovery')


class RegistererError(BaseException):
    pass


class MissingConfigurationError(RegistererError):
    pass


class ServiceCatalogRegistration(object):

    def __init__(self, service_name, config, publisher, check=None):
        self._check = check or self._default_check
        self._registerer = NotifyingRegisterer.from_config(service_name, publisher, config)

        self._retry_interval = config['service_discovery']['retry_interval']
        self._refresh_interval = config['service_discovery']['refresh_interval']

        self._thread = threading.Thread(target=self._loop)
        self._sleep_event = threading.Event()
        self._thread.daemon = True
        self._thread.name = 'ServiceDiscoveryThread'

        self._done = False
        self._registered = False

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, type, value, traceback):
        if type:
            logger.debug('An error occured: %s %s %s', type, value, traceback)

        if self._thread.is_alive():
            logger.debug('waiting for the service discovery thread to complete')
            self._done = True
            self._wake()
            self._thread.join()

        try:
            self._registerer.deregister()
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
        except RegistererError:
            logger.exception('failed to register service')
            logger.info('registration failed, retrying in %s seconds', self._retry_interval)

    def _default_check(self):
        return True


class Registerer(object):

    def __init__(self, name, consul_config, advertise_address, advertise_port, ttl_interval, service_tags):
        self._service_id = str(uuid.uuid4())
        self._service_name = name
        self._advertise_address = advertise_address
        self._advertise_port = advertise_port
        self._tags = service_tags
        self._consul_config = consul_config
        self._ttl_interval = '{}s'.format(ttl_interval)
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
        result = self._client.agent.check.ttl_pass(self._check_id)
        if not result:
            logger('ttl pass failed')
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

    @classmethod
    def _find_address(cls, config):
        advertise_address = config['service_discovery']['advertise_address']
        if advertise_address != 'auto':
            return advertise_address

        iface = config['service_discovery']['advertise_address_interface']
        try:
            return netifaces.ifaddresses(iface)[netifaces.AF_INET][0]['addr']
        except ValueError as e:
            raise RegistererError('{}: {}'.format(str(e), iface))

    @classmethod
    def _canonicalize_config(cls, service_name, config):
        try:
            uuid = config['uuid']
            consul_config = config['consul']
            service_discovery_config = config['service_discovery']
            original_tags = service_discovery_config.get('extra_tags', [])
            service_discovery_config['extra_tags'] = original_tags + [service_name, uuid]
            advertise_address = cls._find_address(config)
            return dict(
                consul_config=consul_config,
                advertise_address=advertise_address,
                advertise_port=service_discovery_config['advertise_port'],
                ttl_interval=service_discovery_config['ttl_interval'],
                service_tags=service_discovery_config['extra_tags'],
            )
        except KeyError as e:
            raise MissingConfigurationError(str(e))

    @classmethod
    def from_config(cls, service_name, config):
        canonicalized_config = cls._canonicalize_config(service_name, config)
        return cls(service_name, **canonicalized_config)


class NotifyingRegisterer(Registerer):

    def __init__(self, name, publisher, consul_config,
                 advertise_address, advertise_port,
                 ttl_interval, service_tags):
        self._publisher = publisher
        super(NotifyingRegisterer, self).__init__(name, consul_config,
                                                  advertise_address, advertise_port,
                                                  ttl_interval, service_tags)

    def register(self):
        super(NotifyingRegisterer, self).register()
        msg = self._new_registered_event()
        self._publisher.publish(msg)

    def deregister(self):
        was_registered = super(NotifyingRegisterer, self).deregister()
        if was_registered:
            msg = self._new_deregistered_event()
            self._publisher.publish(msg)
        return was_registered

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

    @classmethod
    def from_config(cls, service_name, publisher, config):
        canonicalized_config = cls._canonicalize_config(service_name, config)
        return cls(service_name, publisher, **canonicalized_config)
