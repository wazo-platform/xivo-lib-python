# -*- coding: utf-8 -*-

# Copyright (C) 2013 Avencall
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

from hamcrest import assert_that, equal_to

from .. import line_identity


class TestLineIdentity(unittest.TestCase):

    def test_line_identity_from_channel(self):
        channel = 'SIP/tc8nb4-00000004'
        expected_line_identity = 'sip/tc8nb4'

        result = line_identity.identity_from_channel(channel)

        assert_that(result, equal_to(expected_line_identity))

    def test_line_identity_from_channel_local_channels(self):
        local_chan = u'Local/id-292@agentcallback-0000000f;1'
        expected = u'Local/id-292@agentcallback;1'.lower()

        result = line_identity.identity_from_channel(local_chan)

        assert_that(result, equal_to(expected))
