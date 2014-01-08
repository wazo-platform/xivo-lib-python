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

from mock import Mock
from xivo.pubsub import Pubsub


class TestCallNotifier(unittest.TestCase):

    def setUp(self):
        self.pubsub = Pubsub()

    def test_subscribe_and_publish(self):
        callback = Mock()
        message = Mock()
        topic = 'abcd'

        self.pubsub.subscribe(topic, callback)

        self.pubsub.publish(topic, message)
        callback.assert_called_once_with(message)

    def test_multiple_subscribe_on_same_topic_and_one_publish(self):
        callback_1 = Mock()
        callback_2 = Mock()
        message = Mock()
        topic = 'abcd'

        self.pubsub.subscribe(topic, callback_1)
        self.pubsub.subscribe(topic, callback_2)

        self.pubsub.publish(topic, message)
        callback_1.assert_called_once_with(message)
        callback_2.assert_called_once_with(message)

    def test_multiple_subscribe_on_different_topics_and_two_publish(self):
        callback = Mock()
        message_1 = Mock()
        message_2 = Mock()
        topic_1 = 'abcd'
        topic_2 = 'efgh'

        self.pubsub.subscribe(topic_1, callback)
        self.pubsub.subscribe(topic_2, callback)

        self.pubsub.publish(topic_1, message_1)
        callback.assert_any_call(message_1)
        self.assertEquals(callback.call_count, 1)

        self.pubsub.publish(topic_2, message_2)
        callback.assert_any_call(message_2)
        self.assertEquals(callback.call_count, 2)

    def test_unsubscribe_when_never_subscribed(self):
        callback = Mock()
        topic = 'abcd'

        self.pubsub.unsubscribe(topic, callback)

        # Does not raise Exception

    def test_unsubscribed_when_subscribed(self):
        callback = Mock()
        message = Mock()
        topic = 'abcd'
        self.pubsub.subscribe(topic, callback)

        self.pubsub.unsubscribe(topic, callback)

        self.pubsub.publish(topic, message)
        self.assertEquals(callback.call_count, 0)

    def publish_when_nobody_subscribed(self):
        message = Mock()
        topic = 'abcd'

        self.pubsub.publish(topic, message)

        # Does not raise Exception

    def test_unsubscribe_when_multiple_subscribers_on_same_topic(self):
        callback_1 = Mock()
        callback_2 = Mock()
        message = Mock()
        topic = 'abcd'
        self.pubsub.subscribe(topic, callback_1)
        self.pubsub.subscribe(topic, callback_2)

        self.pubsub.unsubscribe(topic, callback_1)

        self.pubsub.publish(topic, message)
        self.assertEquals(callback_1.call_count, 0)
        callback_2.assert_called_once_with(message)
