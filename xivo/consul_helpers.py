# Copyright 2015-2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from types import TracebackType
from typing import Any, TypedDict, TypeVar
from uuid import uuid4

import requests
from consul import Check, Consul, ConsulException
from requests.exceptions import ConnectionError
from wazo_bus.resources.common.abstract import EventProtocol

try:
    import netifaces
except ImportError:
    pass

try:
    from wazo_bus.publisher import BusPublisher
    from wazo_bus.resources.services.event import (
        ServiceDeregisteredEvent,
        ServiceRegisteredEvent,
    )
except ImportError:
    pass


class ConsulService(TypedDict):
    Service: str
    ID: str
    Address: str
    Port: int
    Tags: list[str]


logger = logging.getLogger('service_discovery')
VALID_SERVICE_DISCO_IFACE_PREFIX = ['eth', 'en']


class RegistererError(Exception):
    pass


class ServiceDiscoveryError(Exception):
    pass


class MissingConfigurationError(RegistererError):
    pass


Self = TypeVar('Self', bound='ServiceCatalogRegistration')


class ServiceCatalogRegistration:
    def __init__(
        self,
        service_name: str,
        uuid: str,
        consul_config: dict[str, Any],
        service_discovery_config: dict[str, Any],
        bus_config: dict[str, Any],
        check: Callable[[], bool] | None = None,
    ) -> None:
        self._enabled = service_discovery_config.get('enabled', True)
        if not self._enabled:
            logger.debug('service discovery has been disabled')
            return

        self._check = check or self._default_check
        self._registerer = NotifyingRegisterer(
            service_name, uuid, consul_config, service_discovery_config, bus_config
        )

        self._retry_interval: int = service_discovery_config['retry_interval']
        self._refresh_interval: int = service_discovery_config['refresh_interval']

        self._thread = threading.Thread(target=self._loop)
        self._sleep_event = threading.Event()
        self._thread.daemon = True
        self._thread.name = 'ServiceDiscoveryThread'

        self._done = False
        self._registered = False

    def __enter__(self: Self) -> Self:
        if self._enabled:
            self._thread.start()
        return self

    def __exit__(
        self,
        type: type[BaseException],
        value: BaseException,
        traceback: TracebackType | None,
    ) -> None:
        if type:
            logger.debug('An error occurred: %s %s %s', type, value, traceback)

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

    def _loop(self) -> None:
        while not self._done:
            if not self._registered:
                service_ready = self._check()
                if service_ready:
                    self._register()

            if self._registered and self._registerer.send_ttl():
                self._sleep(self._refresh_interval)
            else:
                self._sleep(self._retry_interval)

    def _sleep(self, interval: int) -> None:
        self._sleep_event.wait(interval)

    def _wake(self) -> None:
        self._sleep_event.set()

    def _register(self) -> None:
        try:
            self._registerer.register()
            self._registered = True
        except RegistererError as e:
            logger.info(
                'registration failed, retrying in %s seconds %s',
                self._retry_interval,
                e,
            )

    def _default_check(self) -> bool:
        return True


class Registerer:
    def __init__(
        self,
        name: str,
        uuid: str,
        consul_config: dict[str, Any],
        service_discovery_config: dict[str, Any],
    ) -> None:
        self._service_id = str(uuid4())
        self._service_name = name
        try:
            self._advertise_address = self._find_address(service_discovery_config)
            self._advertise_port = service_discovery_config['advertise_port']
            self._tags = [uuid, name] + service_discovery_config.get('extra_tags', [])

            self._ttl_interval = f'{service_discovery_config["ttl_interval"]}s'
        except KeyError as e:
            raise MissingConfigurationError(str(e))
        self._consul_config = consul_config
        self._check_id = f'service:{self._service_id}'

    @property
    def _client(self) -> Consul:
        return Consul(**self._consul_config)

    def register(self) -> None:
        logger.info(
            'Registering %s on Consul as %s with %s:%s',
            self._service_name,
            self._service_id,
            self._advertise_address,
            self._advertise_port,
        )

        try:
            ttl_check = Check.ttl(self._ttl_interval)
            registered = self._client.agent.service.register(
                self._service_name,
                service_id=self._service_id,
                address=self._advertise_address,
                port=self._advertise_port,
                check=ttl_check,
                tags=self._tags,
            )
            if not registered:
                raise RegistererError(
                    f'{self._service_name} registration on Consul failed'
                )

        except (ConnectionError, ConsulException) as e:
            raise RegistererError(str(e))

    def send_ttl(self) -> bool | None:
        result = None

        try:
            result = self._client.agent.check.ttl_pass(self._check_id)
        except (ConnectionError, ConsulException) as e:
            logger.info('%s', e)

        if not result:
            logger.info('ttl pass failed')

        return result

    def deregister(self) -> bool | None:
        logger.info(
            'Deregistering %s from Consul services: %s',
            self._service_name,
            self._service_id,
        )

        try:
            client = self._client
            client.agent.check.deregister(self._check_id)
            return client.agent.service.deregister(self._service_id)
        except (ConnectionError, ConsulException) as e:
            raise RegistererError(str(e))

    def _find_address(self, service_discovery_config: dict[str, Any]) -> str:
        return address_from_config(service_discovery_config)


def address_from_config(service_discovery_config: dict[str, Any]) -> str:
    advertise_address = service_discovery_config['advertise_address']
    if advertise_address != 'auto':
        return advertise_address
    return _find_address(service_discovery_config['advertise_address_interface'])


def _find_address(main_iface: str) -> str:
    def _is_valid_iface_name(name: str) -> bool:
        for prefix in VALID_SERVICE_DISCO_IFACE_PREFIX:
            if name.startswith(prefix):
                return True
        return False

    ifaces = (
        [main_iface]
        + [iface for iface in netifaces.interfaces() if _is_valid_iface_name(iface)]
        + ['lo']
    )
    for iface in ifaces:
        try:
            for config in netifaces.ifaddresses(iface).get(netifaces.AF_INET, []):
                if address := config.get('addr'):
                    return address
        except ValueError:
            logger.info('The configured interface does not exists: %s', iface)

    return '127.0.0.1'


class NotifyingRegisterer(Registerer):
    def __init__(
        self,
        name: str,
        uuid: str,
        consul_config: dict[str, Any],
        service_discovery_config: dict[str, Any],
        bus_config: dict[str, Any],
    ) -> None:
        super().__init__(name, uuid, consul_config, service_discovery_config)
        self._publisher = BusPublisher(
            name='consul-helper', service_uuid=uuid, **bus_config
        )

    def register(self) -> None:
        super().register()
        event = ServiceRegisteredEvent(
            self._service_name,
            self._service_id,
            self._advertise_address,
            self._advertise_port,
            self._tags,
        )
        self._notify(event)

    def deregister(self) -> bool | None:
        exception = None
        try:
            should_send_msg = super().deregister()
        except RegistererError as e:
            should_send_msg = True
            exception = e

        if should_send_msg:
            event = ServiceDeregisteredEvent(
                self._service_name, self._service_id, self._tags
            )
            self._notify(event)

        if exception:
            raise exception

        return should_send_msg

    def _notify(self, event: EventProtocol) -> None:
        self._publisher.publish(event)


class ServiceFinder:
    def __init__(self, consul_config: dict[str, Any]) -> None:
        self._dc_url = '{scheme}://{host}:{port}/v1/catalog/datacenters'.format(
            **consul_config
        )
        self._health_url = '{scheme}://{host}:{port}/v1/health/service'.format(
            **consul_config
        )
        self._service_url = '{scheme}://{host}:{port}/v1/catalog/service'.format(
            **consul_config
        )
        self._verify = consul_config.get('verify', True)
        self._token = consul_config.get('token')

    def list_healthy_services(
        self, service_name: str, xivo_uuid: str | None = None
    ) -> list[ConsulService]:
        services = []
        for dc in self._get_datacenters():
            for service in self._list_running_services(service_name, dc, tag=xivo_uuid):
                services.append(service)
        return services

    def _get_datacenters(self) -> dict[str, Any]:
        response = requests.get(self._dc_url, verify=self._verify)
        self._assert_ok(response)
        return response.json()

    def _list_running_services(
        self, service_name: str, datacenter: str, tag: str | None
    ) -> list[ConsulService]:
        url = f'{self._health_url}/{service_name}'
        params: dict[str, str | bool] = {'dc': datacenter, 'passing': True}
        if tag:
            params['tag'] = tag
        response = requests.get(url, verify=self._verify, params=params)
        self._assert_ok(response)
        services = []
        for node in response.json():
            service: ConsulService | None = node.get('Service')
            if service:
                services.append(service)
        return services

    @staticmethod
    def _assert_ok(response: requests.Response, code: int = 200) -> None:
        if response.status_code != code:
            msg = getattr(response, 'text', 'unknown error')
            raise ServiceDiscoveryError(msg)
