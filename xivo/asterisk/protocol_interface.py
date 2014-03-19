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

channel_regexp = re.compile(r'(sip|sccp|local)/([\w@-]+)-', re.I)


ProtocolInterface = collections.namedtuple('ProtocolInterface', ['protocol', 'interface'])


class InvalidChannelError(ValueError):

    def __init__(self, invalid_channel):
        ValueError.__init__(self, 'the channel %s is invalid' % invalid_channel)


def protocol_interface_from_channel(channel):
    matches = channel_regexp.match(channel)
    if matches is None:
        raise InvalidChannelError(channel)

    protocol = matches.group(1)
    interface = matches.group(2)

    return ProtocolInterface(protocol, interface)
