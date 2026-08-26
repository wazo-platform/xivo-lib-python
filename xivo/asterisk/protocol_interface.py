# Copyright 2013-2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import re
from collections.abc import Generator
from typing import NamedTuple

# A channel name is <tech>/<resource><discriminator>, where the discriminator is what
# each channel driver appends to make the name unique. Most techs use -<uniqueid>, a
# hexadecimal counter (PJSIP/Local '%08x', DAHDI '%x', IAX2 a decimal call number),
# with Local channels adding ;<leg> for their two halves. chan_websocket instead uses
# /%p, the channel pointer. The resource is tech-specific and unconstrained: whatever
# lies between the technology and the discriminator belongs to it.
channel_regexp = re.compile(
    r'(pjsip|sip|sccp|local|dahdi|iax2|websocket)/(.+)'
    r'(?:-[0-9a-f]+(?:;\d+)?|/0x[0-9a-f]+)$',
    re.I,
)
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
        protocol = 'SIP' if protocol.isupper() else 'sip'
    return ProtocolInterface(protocol, interface)


def protocol_interfaces_from_hint(
    hint: str, ignore_invalid: bool = True
) -> Generator[ProtocolInterface]:
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
