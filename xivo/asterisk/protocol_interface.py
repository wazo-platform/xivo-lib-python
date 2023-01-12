# Copyright 2013-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import re

from typing import NamedTuple, Generator

channel_regexp = re.compile(r'(pjsip|sip|sccp|local|dahdi|iax2)/([*\w@/-]+)-', re.I)
agent_channel_regex = re.compile(r'Local/id-(\d+)@agentcallback')
device_regexp = re.compile(r'(sip|sccp|local|dahdi|iax2)/([\w@/-]+)', re.I)


class ProtocolInterface(NamedTuple):
    protocol: str
    interface: str


class InvalidChannelError(ValueError):
    def __init__(self, invalid_channel: str | None = None) -> None:
        super().__init__(self, f'the channel {invalid_channel} is invalid')


def protocol_interface_from_channel(channel: str) -> ProtocolInterface:
    matches = channel_regexp.search(channel)
    if matches is None:
        raise InvalidChannelError(channel)

    protocol = matches.group(1)
    interface = matches.group(2)

    if protocol == 'pjsip':
        protocol = 'sip'
    elif protocol == 'PJSIP':
        protocol = 'SIP'

    return ProtocolInterface(protocol, interface)


def protocol_interfaces_from_hint(
    hint: str, ignore_invalid: bool = True
) -> Generator[ProtocolInterface, None, None]:
    for device in hint.split('&'):
        protocol_interface = _protocol_interface_from_device(device)
        if protocol_interface:
            yield protocol_interface
        elif not ignore_invalid:
            raise InvalidChannelError(device)


def _protocol_interface_from_device(device: str) -> ProtocolInterface | None:
    matches = device_regexp.match(device)
    if matches is None:
        return None

    protocol = matches.group(1)
    interface = matches.group(2)

    return ProtocolInterface(protocol, interface)


def agent_id_from_channel(channel: str) -> int:
    matches = agent_channel_regex.match(channel)
    if matches is None:
        raise InvalidChannelError(channel)

    return int(matches.group(1))
