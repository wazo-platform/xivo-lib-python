# -*- coding: utf-8 -*-

# Copyright (C) 2013-2016 Avencall
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

from hamcrest import assert_that, contains

from ..protocol_interface import ProtocolInterface
from ..protocol_interface import InvalidChannelError
from ..protocol_interface import protocol_interface_from_channel
from ..protocol_interface import protocol_interfaces_from_hint
from ..protocol_interface import agent_id_from_channel


class TestProtocolInterface(unittest.TestCase):

    def test_protocol_interfaces_from_hint(self):
        hint = 'SIP/askdjhf'
        expected_result = ProtocolInterface('SIP', 'askdjhf')

        result = protocol_interfaces_from_hint(hint)

        assert_that(result, contains(expected_result))

    def test_protocol_interfaces_from_multidevice_hint(self):
        hint = 'SIP/line1&SIP/line2'
        expected_result = [ProtocolInterface('SIP', 'line1'),
                           ProtocolInterface('SIP', 'line2')]

        result = protocol_interfaces_from_hint(hint)

        assert_that(result, contains(*expected_result))

    def test_protocol_interfaces_from_hint_invalid(self):
        hint = 'meetme:4001&SIP/line1'
        expected_result = ProtocolInterface('SIP', 'line1')

        result = protocol_interfaces_from_hint(hint)

        assert_that(result, contains(expected_result))

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

    def test_protocol_interface_from_channel_async_goto(self):
        channel = 'AsyncGoto/SCCP/1011-0000007c'
        expected_result = ProtocolInterface('SCCP', '1011')

        result = protocol_interface_from_channel(channel)

        self.assertEquals(expected_result, result)

    def test_protocol_interface_from_channel_dahdi(self):
        channel = 'DAHDI/i1/1042-7'
        expected_result = ProtocolInterface('DAHDI', 'i1/1042')

        result = protocol_interface_from_channel(channel)

        self.assertEquals(expected_result, result)

    def test_protocol_interface_from_channel_iax(self):
        channel = 'IAX2/pigjkls-5304'
        expected_result = ProtocolInterface('IAX2', 'pigjkls')

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

    def test_agent_id_from_channel(self):
        channel = 'Local/id-55@agentcallback-00000001;2'
        expected_id = 55

        result = agent_id_from_channel(channel)

        self.assertEquals(result, expected_id)

    def test_agent_id_from_channel_invalid(self):
        channel = 'asjasldfkjag\'fghdfl48u4'

        self.assertRaises(InvalidChannelError, agent_id_from_channel, channel)

    def test_dash_in_trunk_name(self):
        channel = 'SIP/test-my-trunk-00b167'

        expected_result = ProtocolInterface('SIP', 'test-my-trunk')

        result = protocol_interface_from_channel(channel)

        self.assertEquals(result, expected_result)
