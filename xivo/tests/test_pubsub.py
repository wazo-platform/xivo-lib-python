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

from hamcrest import assert_that
from hamcrest import not_
from mock import Mock
from mock import patch
from xivo.pubsub import Pubsub
from xivo.pubsub import ExceptionLoggingPubsub

SOME_TOPIC = 'abcd'
SOME_MESSAGE = 'defg'


class TestPubsub(unittest.TestCase):

    def setUp(self):
        self.pubsub = Pubsub()

    def test_subscribe_and_publish(self):
        callback = Mock()
        self.pubsub.subscribe(SOME_TOPIC, callback)

        self.pubsub.publish(SOME_TOPIC, SOME_MESSAGE)

        callback.assert_called_once_with(SOME_MESSAGE)

    def test_multiple_subscribe_on_same_topic_and_one_publish(self):
        callback_1 = Mock()
        callback_2 = Mock()
        self.pubsub.subscribe(SOME_TOPIC, callback_1)
        self.pubsub.subscribe(SOME_TOPIC, callback_2)

        self.pubsub.publish(SOME_TOPIC, SOME_MESSAGE)

        callback_1.assert_called_once_with(SOME_MESSAGE)
        callback_2.assert_called_once_with(SOME_MESSAGE)

    def test_multiple_subscribe_on_different_topics_and_two_publish(self):
        callback = Mock()
        message_1 = Mock()
        message_2 = Mock()
        topic_1 = 'abcd'
        topic_2 = 'efgh'
        self.pubsub.subscribe(topic_1, callback)
        self.pubsub.subscribe(topic_2, callback)

        self.pubsub.publish(topic_1, message_1)
        self.pubsub.publish(topic_2, message_2)

        callback.assert_any_call(message_1)
        callback.assert_any_call(message_2)
        self.assertEquals(callback.call_count, 2)

    def test_unsubscribe_when_never_subscribed(self):
        callback = Mock()

        try:
            self.pubsub.unsubscribe(SOME_TOPIC, callback)
        except Exception:
            self.fail('unsubscribe should not raise exceptions')
            raise

    def test_unsubscribed_when_subscribed(self):
        callback = Mock()
        self.pubsub.subscribe(SOME_TOPIC, callback)

        self.pubsub.unsubscribe(SOME_TOPIC, callback)
        self.pubsub.publish(SOME_TOPIC, SOME_MESSAGE)

        self.assertEquals(callback.call_count, 0)

    def publish_when_nobody_subscribed(self):
        try:
            self.pubsub.publish(SOME_TOPIC, SOME_MESSAGE)
        except Exception:
            self.fail('publish should not raise exceptions')
            raise

    def test_unsubscribe_when_multiple_subscribers_on_same_topic(self):
        callback_1 = Mock()
        callback_2 = Mock()
        self.pubsub.subscribe(SOME_TOPIC, callback_1)
        self.pubsub.subscribe(SOME_TOPIC, callback_2)

        self.pubsub.unsubscribe(SOME_TOPIC, callback_1)
        self.pubsub.publish(SOME_TOPIC, SOME_MESSAGE)

        assert_that(not_(callback_1.called))
        callback_2.assert_called_once_with(SOME_MESSAGE)


class TestExceptionLoggingPubsub(unittest.TestCase):

    def setUp(self):
        self.pubsub = ExceptionLoggingPubsub()

    @patch('xivo.pubsub.logger')
    def test_when_exception_then_exception_is_logged(self, logger):
        callback = Mock()
        exception = callback.side_effect = Exception()
        self.pubsub.subscribe(SOME_TOPIC, callback)

        self.pubsub.publish(SOME_TOPIC, SOME_MESSAGE)

        logger.exception.assert_called_once_with(exception)

    @patch('xivo.pubsub.logger', Mock())
    def test_when_exception_then_other_callbacks_are_run(self):
        callback_1, callback_2, callback_3 = Mock(), Mock(), Mock()
        callback_2.side_effect = Exception()
        self.pubsub.subscribe(SOME_TOPIC, callback_1)
        self.pubsub.subscribe(SOME_TOPIC, callback_2)
        self.pubsub.subscribe(SOME_TOPIC, callback_3)

        self.pubsub.publish(SOME_TOPIC, SOME_MESSAGE)

        assert_that(callback_1.called)
        assert_that(callback_3.called)
