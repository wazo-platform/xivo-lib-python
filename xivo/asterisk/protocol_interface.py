# -*- coding: utf-8 -*-
# Copyright (C) 2013-2016 Avencall
# SPDX-License-Identifier: GPL-3.0-or-later

import collections
import re

channel_regexp = re.compile(r'(sip|sccp|local|dahdi|iax2)/([\w@/-]+)-', re.I)
agent_channel_regex = re.compile(r'Local/id-(\d+)@agentcallback')
device_regexp = re.compile(r'(sip|sccp|local|dahdi|iax2)/([\w@/-]+)', re.I)


ProtocolInterface = collections.namedtuple('ProtocolInterface', ['protocol', 'interface'])


class InvalidChannelError(ValueError):

    def __init__(self, invalid_channel=None):
        ValueError.__init__(self, 'the channel %s is invalid' % invalid_channel)


def protocol_interface_from_channel(channel):
    matches = channel_regexp.search(channel)
    if matches is None:
        raise InvalidChannelError(channel)

    protocol = matches.group(1)
    interface = matches.group(2)

    return ProtocolInterface(protocol, interface)


def protocol_interfaces_from_hint(hint, ignore_invalid=True):
    for device in hint.split('&'):
        protocol_interface = _protocol_interface_from_device(device)
        if protocol_interface:
            yield protocol_interface
        elif not ignore_invalid:
            raise InvalidChannelError(device)


def _protocol_interface_from_device(device):
    matches = device_regexp.match(device)
    if matches is None:
        return None

    protocol = matches.group(1)
    interface = matches.group(2)

    return ProtocolInterface(protocol, interface)



def agent_id_from_channel(channel):
    matches = agent_channel_regex.match(channel)
    if matches is None:
        raise InvalidChannelError(channel)

    return int(matches.group(1))
