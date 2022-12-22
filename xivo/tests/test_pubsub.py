# Copyright 2013-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from hamcrest import (
    assert_that,
    is_,
)
from unittest.mock import Mock, patch

from ..pubsub import Pubsub, CallbackCollector

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
        self.assertEqual(callback.call_count, 2)

    def test_unsubscribe_when_never_subscribed(self):
        callback = Mock()

        try:
            self.pubsub.unsubscribe(SOME_TOPIC, callback)
        except Exception:
            self.fail('unsubscribe should not raise exceptions')

    def test_unsubscribed_when_subscribed(self):
        callback = Mock()
        self.pubsub.subscribe(SOME_TOPIC, callback)

        self.pubsub.unsubscribe(SOME_TOPIC, callback)
        self.pubsub.publish(SOME_TOPIC, SOME_MESSAGE)

        self.assertEqual(callback.call_count, 0)

    def publish_when_nobody_subscribed(self):
        try:
            self.pubsub.publish(SOME_TOPIC, SOME_MESSAGE)
        except Exception:
            self.fail('publish should not raise exceptions')

    def test_unsubscribe_when_multiple_subscribers_on_same_topic(self):
        callback_1 = Mock()
        callback_2 = Mock()
        self.pubsub.subscribe(SOME_TOPIC, callback_1)
        self.pubsub.subscribe(SOME_TOPIC, callback_2)

        self.pubsub.unsubscribe(SOME_TOPIC, callback_1)
        self.pubsub.publish(SOME_TOPIC, SOME_MESSAGE)

        assert_that(callback_1.called, is_(False))
        callback_2.assert_called_once_with(SOME_MESSAGE)

    def test_when_exception_then_exception_is_handled(self):
        callback = Mock()
        exception = callback.side_effect = Exception()
        handler = Mock()
        self.pubsub.set_exception_handler(handler)
        self.pubsub.subscribe(SOME_TOPIC, callback)

        self.pubsub.publish(SOME_TOPIC, SOME_MESSAGE)

        handler.assert_called_once_with(callback, SOME_MESSAGE, exception)

    @patch('xivo.pubsub.logger')
    def test_when_exception_then_exception_is_logged_by_default(self, logger):
        callback = Mock()
        exception = callback.side_effect = Exception()
        self.pubsub.subscribe(SOME_TOPIC, callback)

        self.pubsub.publish(SOME_TOPIC, SOME_MESSAGE)

        logger.exception.assert_called_once_with(exception)

    def test_when_exception_then_other_callbacks_are_run(self):
        callback_1, callback_2, callback_3 = Mock(), Mock(), Mock()
        callback_2.side_effect = Exception()
        self.pubsub.subscribe(SOME_TOPIC, callback_1)
        self.pubsub.subscribe(SOME_TOPIC, callback_2)
        self.pubsub.subscribe(SOME_TOPIC, callback_3)

        self.pubsub.publish(SOME_TOPIC, SOME_MESSAGE)

        assert_that(callback_1.called)
        assert_that(callback_3.called)


class TestCallbackCollector(unittest.TestCase):
    def setUp(self):
        self.callback_collector = CallbackCollector()

    def test_subscribe_and_source_callback(self):
        callback = Mock()
        source_callback_1 = self.callback_collector.new_source()
        self.callback_collector.subscribe(callback)

        source_callback_1()

        callback.assert_called_once_with()

    def test_subscribe_and_multiple_source_callbacks(self):
        callback = Mock()
        source_callback_1 = self.callback_collector.new_source()
        source_callback_2 = self.callback_collector.new_source()
        source_callback_3 = self.callback_collector.new_source()
        self.callback_collector.subscribe(callback)

        source_callback_2()
        callback.assert_not_called()

        source_callback_3()
        callback.assert_not_called()

        source_callback_1()
        callback.assert_called_once_with()

    def test_multiple_subscribes_and_source_callback(self):
        callback_1 = Mock()
        callback_2 = Mock()
        source_callback = self.callback_collector.new_source()
        self.callback_collector.subscribe(callback_1)
        self.callback_collector.subscribe(callback_2)

        source_callback()
        callback_1.assert_called_once_with()
        callback_2.assert_called_once_with()

    def test_multiple_subscribes_and_multiple_source_callbacks(self):
        callback_1 = Mock()
        callback_2 = Mock()
        source_callback_1 = self.callback_collector.new_source()
        source_callback_2 = self.callback_collector.new_source()
        source_callback_3 = self.callback_collector.new_source()
        self.callback_collector.subscribe(callback_1)
        self.callback_collector.subscribe(callback_2)

        source_callback_2()
        callback_1.assert_not_called()
        callback_2.assert_not_called()

        source_callback_3()
        callback_1.assert_not_called()
        callback_2.assert_not_called()

        source_callback_1()
        callback_1.assert_called_once_with()
        callback_2.assert_called_once_with()

    def test_when_subscribe_raise_exception_then_exception_is_handled(self):
        callback = Mock()
        callback.side_effect = Exception()
        handler = Mock()
        self.callback_collector._pubsub.set_exception_handler(handler)
        source_callback = self.callback_collector.new_source()
        self.callback_collector.subscribe(callback)

        source_callback()
        handler.assert_called_once()
