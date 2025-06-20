# Copyright 2013-2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from hamcrest import assert_that, contains_exactly

from ..protocol_interface import (
    InvalidChannelError,
    ProtocolInterface,
    agent_id_from_channel,
    protocol_interface_from_channel,
    protocol_interfaces_from_hint,
)


class TestProtocolInterface(unittest.TestCase):
    def test_protocol_interfaces_from_hint(self):
        hint = 'SIP/askdjhf'
        expected_result = ProtocolInterface('SIP', 'askdjhf')

        result = protocol_interfaces_from_hint(hint)

        assert_that(result, contains_exactly(expected_result))

    def test_protocol_interfaces_from_multidevice_hint(self):
        hint = 'SIP/line1&SIP/line2'
        expected_result = [
            ProtocolInterface('SIP', 'line1'),
            ProtocolInterface('SIP', 'line2'),
        ]

        result = protocol_interfaces_from_hint(hint)

        assert_that(result, contains_exactly(*expected_result))

    def test_protocol_interfaces_from_hint_invalid(self):
        hint = 'conference:4001&SIP/line1'
        expected_result = ProtocolInterface('SIP', 'line1')

        result = protocol_interfaces_from_hint(hint)

        assert_that(result, contains_exactly(expected_result))

    def test_protocol_interface_from_channel_pjsip_lower(self):
        channel = 'pjsip/askdjhf-3216549'
        expected_result = ProtocolInterface('sip', 'askdjhf')

        result = protocol_interface_from_channel(channel)

        self.assertEqual(expected_result, result)

    def test_protocol_interface_from_channel_pjsip(self):
        channel = 'PJSIP/askdjhf-3216549'
        expected_result = ProtocolInterface('SIP', 'askdjhf')

        result = protocol_interface_from_channel(channel)

        self.assertEqual(expected_result, result)

    def test_protocol_interface_from_channel_sip(self):
        channel = 'SIP/askdjhf-3216549'
        expected_result = ProtocolInterface('SIP', 'askdjhf')

        result = protocol_interface_from_channel(channel)

        self.assertEqual(expected_result, result)

    def test_protocol_interface_from_channel_sccp(self):
        channel = 'SCCP/13486-00000658'
        expected_result = ProtocolInterface('SCCP', '13486')

        result = protocol_interface_from_channel(channel)

        self.assertEqual(expected_result, result)

    def test_protocol_interface_from_channel_async_goto(self):
        channel = 'AsyncGoto/SCCP/1011-0000007c'
        expected_result = ProtocolInterface('SCCP', '1011')

        result = protocol_interface_from_channel(channel)

        self.assertEqual(expected_result, result)

    def test_protocol_interface_from_channel_dahdi(self):
        channel = 'DAHDI/i1/1042-7'
        expected_result = ProtocolInterface('DAHDI', 'i1/1042')

        result = protocol_interface_from_channel(channel)

        self.assertEqual(expected_result, result)

    def test_protocol_interface_from_channel_iax(self):
        channel = 'IAX2/pigjkls-5304'
        expected_result = ProtocolInterface('IAX2', 'pigjkls')

        result = protocol_interface_from_channel(channel)

        self.assertEqual(expected_result, result)

    def test_protocol_interface_from_channel_invalid(self):
        invalid_channel = 'slkdfjaslkdjfaslkdjflskdjf'

        self.assertRaises(
            InvalidChannelError, protocol_interface_from_channel, invalid_channel
        )

    def test_with_a_local_channel(self):
        local_channel = 'Local/id-5@agentcallback-00000001;2'
        expected_result = ProtocolInterface('Local', 'id-5@agentcallback')

        result = protocol_interface_from_channel(local_channel)

        self.assertEqual(result, expected_result)

    def test_agent_id_from_channel(self):
        channel = 'Local/id-55@agentcallback-00000001;2'
        expected_id = 55

        result = agent_id_from_channel(channel)

        self.assertEqual(result, expected_id)

    def test_agent_id_from_channel_invalid(self):
        channel = 'asjasldfkjag\'fghdfl48u4'

        self.assertRaises(InvalidChannelError, agent_id_from_channel, channel)

    def test_dash_in_trunk_name(self):
        channel = 'SIP/test-my-trunk-00b167'

        expected_result = ProtocolInterface('SIP', 'test-my-trunk')

        result = protocol_interface_from_channel(channel)

        self.assertEqual(result, expected_result)

    def test_star_code_in_interface(self):
        channel = 'Local/**96**996666@internal-00000006;1'

        expected_result = ProtocolInterface('Local', '**96**996666@internal')

        result = protocol_interface_from_channel(channel)

        self.assertEqual(result, expected_result)

    def test_plus_sign_in_interface(self):
        channel = 'Local/+33999999999@default-00005df6;1'

        expected_result = ProtocolInterface('Local', '+33999999999@default')

        result = protocol_interface_from_channel(channel)

        self.assertEqual(result, expected_result)

    def test_pound_sign_in_interface(self):
        channel = 'Local/##42@default-00005df6;1'

        expected_result = ProtocolInterface('Local', '##42@default')

        result = protocol_interface_from_channel(channel)

        self.assertEqual(result, expected_result)

    def test_pipe_sign_in_interface(self):
        channel = 'Local/123|*42@default-00005df6;1'

        expected_result = ProtocolInterface('Local', '123|*42@default')

        result = protocol_interface_from_channel(channel)

        self.assertEqual(result, expected_result)
