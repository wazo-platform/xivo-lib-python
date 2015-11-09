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

import logging
import uuid

from consul import Check, Consul, ConsulException
from requests.exceptions import ConnectionError
try:
    # xivo_bus is an optional dependency
    from xivo_bus.resources.services import event
except ImportError:
    pass


class RegistererError(BaseException):
    pass


class MissingConfigurationError(RegistererError):
    pass


class Registerer(object):

    def __init__(self, name, consul_config, advertise_address, advertise_port,
                 check_url, check_url_timeout, check_url_interval, service_tags):
        self._service_id = str(uuid.uuid4())
        self._service_name = name
        self._advertise_address = advertise_address
        self._advertise_port = advertise_port
        self._tags = service_tags
        self._consul_config = consul_config
        self._check_id = str(uuid.uuid4())
        self._check_url = check_url
        self._check_url_interval = check_url_interval
        self._check_url_timeout = check_url_timeout
        self._logger = logging.getLogger(name)

    @property
    def _client(self):
        return Consul(**self._consul_config)

    def register(self):
        self._logger.info('Registering %s on Consul as %s with %s:%s',
                          self._service_name,
                          self._service_id,
                          self._advertise_address,
                          self._advertise_port)

        try:
            http_check = Check.http(self._check_url, self._check_url_interval, timeout=self._check_url_timeout)
            registered = self._client.agent.service.register(self._service_name,
                                                             service_id=self._service_id,
                                                             address=self._advertise_address,
                                                             port=self._advertise_port,
                                                             check=http_check,
                                                             tags=self._tags)
            if not registered:
                raise RegistererError('{} registration on Consul failed'.format(self._service_name))

        except (ConnectionError, ConsulException) as e:
            raise RegistererError(str(e))

    def deregister(self):
        self._logger.info('Deregistering %s from Consul services: %s',
                          self._service_name,
                          self._service_id)

        try:
            return self._client.agent.service.deregister(self._service_id)
        except (ConnectionError, ConsulException) as e:
            raise RegistererError(str(e))

    @staticmethod
    def _canonicalize_config(service_name, config):
        try:
            uuid = config['uuid']
            consul_config = config['consul']
            service_discovery_config = config['service_discovery']
            original_tags = service_discovery_config.get('extra_tags', [])
            service_discovery_config['extra_tags'] = original_tags + [service_name, uuid]
            return dict(
                consul_config=consul_config,
                advertise_address=service_discovery_config['advertise_address'],
                advertise_port=service_discovery_config['advertise_port'],
                check_url=service_discovery_config['check_url'],
                check_url_timeout=service_discovery_config['check_url_timeout'],
                check_url_interval=service_discovery_config['check_url_interval'],
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
                 check_url, check_url_timeout, check_url_interval, service_tags):
        self._publisher = publisher
        super(NotifyingRegisterer, self).__init__(name, consul_config,
                                                  advertise_address, advertise_port,
                                                  check_url, check_url_timeout, check_url_interval,
                                                  service_tags)

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
