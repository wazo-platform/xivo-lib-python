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

from consul import Check, Consul


class Registerer(object):

    def __init__(self, name, host, port, token, advertise_address, advertise_port,
                 check_url, check_url_timeout, service_tags, **kwargs):
        self._service_id = str(uuid.uuid4())
        self._service_name = name
        self._advertise_address = advertise_address
        self._advertise_port = advertise_port
        self._tags = service_tags
        self._consul_host = host
        self._consul_port = port
        self._consul_token = token
        self._check_id = str(uuid.uuid4())
        self._check_url = check_url
        self._check_url_timeout = check_url_timeout
        self._logger = logging.getLogger(name)

    @property
    def _client(self):
        return Consul(self._consul_host, self._consul_port, self._consul_token)

    def register(self):
        self._logger.info('Registering %s on Consul as %s with %s:%s',
                          self._service_name,
                          self._service_id,
                          self._advertise_address,
                          self._advertise_port)

        http_check = Check.http(self._check_url, self._check_url_timeout)
        self._client.agent.service.register(self._service_name,
                                            service_id=self._service_id,
                                            address=self._advertise_address,
                                            port=self._advertise_port,
                                            check=http_check,
                                            tags=self._tags)

    def deregister(self):
        self._logger.info('Deregistering %s from Consul services: %s',
                          self._service_name,
                          self._service_id)

        self._client.agent.service.deregister(self._service_id)

    def is_registered(self):
        _, services = self._client.catalog.service(self._service_name)
        return any(service['ServiceID'] == self._service_id for service in services)
