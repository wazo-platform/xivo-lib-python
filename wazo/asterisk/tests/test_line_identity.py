# Copyright 2013-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from hamcrest import assert_that, equal_to

from .. import line_identity


class TestLineIdentity(unittest.TestCase):
    def test_line_identity_from_channel(self):
        channel = 'SIP/tc8nb4-00000004'
        expected_line_identity = 'sip/tc8nb4'

        result = line_identity.identity_from_channel(channel)

        assert_that(result, equal_to(expected_line_identity))

    def test_line_identity_from_channel_local_channels(self):
        local_chan = 'Local/id-292@agentcallback-0000000f;1'
        expected = 'Local/id-292@agentcallback;1'.lower()

        result = line_identity.identity_from_channel(local_chan)

        assert_that(result, equal_to(expected))
