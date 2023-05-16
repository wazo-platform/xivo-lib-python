# Copyright 2013-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import re
from typing import NamedTuple
from collections.abc import Generator

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
    if (match := channel_regexp.search(channel)) is None:
        raise InvalidChannelError(channel)

    protocol, interface = match.groups()
    if protocol.lower() == 'pjsip':
        protocol = protocol[-3:]
    return ProtocolInterface(protocol, interface)


def protocol_interfaces_from_hint(
    hint: str, ignore_invalid: bool = True
) -> Generator[ProtocolInterface, None, None]:
    for device in hint.split('&'):
        if protocol_interface := _protocol_interface_from_device(device):
            yield protocol_interface
        elif not ignore_invalid:
            raise InvalidChannelError(device)


def _protocol_interface_from_device(device: str) -> ProtocolInterface | None:
    if (match := device_regexp.match(device)) is None:
        return None
    protocol, interface = match.groups()
    return ProtocolInterface(protocol, interface)


def agent_id_from_channel(channel: str) -> int:
    if (match := agent_channel_regex.match(channel)) is None:
        raise InvalidChannelError(channel)
    return int(match.group(1))
