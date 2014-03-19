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

import unittest

from xivo.asterisk.protocol_interface import ProtocolInterface
from xivo.asterisk.protocol_interface import InvalidChannelError
from xivo.asterisk.protocol_interface import protocol_interface_from_channel


class TestProtocolInterface(unittest.TestCase):

    def test_protocol_interface_from_channel_sip(self):
        channel = 'SIP/askdjhf-3216549'
        expected_result = ProtocolInterface('SIP', 'askdjhf')

        result = protocol_interface_from_channel(channel)

        self.assertEquals(expected_result, result)

    def test_protocol_interface_from_channel_sccp(self):
        channel = 'SCCP/13486-00000658'
        expected_result = ProtocolInterface('SCCP', '13486')

        result = protocol_interface_from_channel(channel)

        self.assertEquals(expected_result, result)

    def test_protocol_interface_from_channel_invalid(self):
        invalid_channel = 'slkdfjaslkdjfaslkdjflskdjf'

        self.assertRaises(InvalidChannelError, protocol_interface_from_channel, invalid_channel)

    def test_with_a_local_channel(self):
        local_channel = 'Local/id-5@agentcallback-00000001;2'
        expected_result = ProtocolInterface('Local', 'id-5@agentcallback')

        result = protocol_interface_from_channel(local_channel)

        self.assertEquals(result, expected_result)
