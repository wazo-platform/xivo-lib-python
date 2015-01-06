# -*- coding: utf-8 -*-

# Copyright (C) 2013-2014 Avencall
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

import collections
import re

channel_regexp = re.compile(r'(sip|sccp|local|dahdi|iax2)/([\w@/-]+)-', re.I)
agent_channel_regex = re.compile(r'Local/id-(\d+)@agentcallback')
hint_regexp = re.compile(r'(sip|sccp|local|dahdi|iax2)/([\w@/-]+)', re.I)


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


def protocol_interface_from_hint(hint):
    matches = hint_regexp.search(hint)
    if matches is None:
        raise InvalidChannelError(hint)

    protocol = matches.group(1)
    interface = matches.group(2)

    return ProtocolInterface(protocol, interface)



def agent_id_from_channel(channel):
    matches = agent_channel_regex.match(channel)
    if matches is None:
        raise InvalidChannelError(channel)

    return int(matches.group(1))
