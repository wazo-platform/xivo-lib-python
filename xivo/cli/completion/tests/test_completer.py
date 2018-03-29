# -*- coding: utf-8 -*-
# Copyright (C) 2013-2014 Avencall
# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

import unittest
from mock import Mock
from hamcrest import assert_that, equal_to
from xivo.cli.completion.completer import CommandLineCompleter
from xivo.cli.registry import CommandRegistry


class TestCompleter(unittest.TestCase):

    def setUp(self):
        self.command_registry = Mock(CommandRegistry)
        self.command_registry.complete_next_word.return_value = ['agents', 'users']
        self.completer = CommandLineCompleter(self.command_registry)

    def test_complete_next_word_empty_line(self):
        words = []

        candidates = self.completer.complete_next_word(words)

        self.command_registry.complete_next_word.assert_called_once_with([])
        assert_that(candidates, equal_to(['agents', 'users']))

    def test_complete_last_word_one_valid_letter(self):
        words = ['a']

        candidates = self.completer.complete_last_word(words)

        self.command_registry.complete_next_word.assert_called_once_with([])
        assert_that(candidates, equal_to(['agents']))

    def test_complete_last_word_one_invalid_letter(self):
        words = ['x']

        candidates = self.completer.complete_last_word(words)

        self.command_registry.complete_next_word.assert_called_once_with([])
        assert_that(candidates, equal_to([]))

    def test_complete_last_word_one_valid_word(self):
        words = ['agents']

        candidates = self.completer.complete_last_word(words)

        self.command_registry.complete_next_word.assert_called_once_with([])
        assert_that(candidates, equal_to(['agents']))

    def test_complete_next_word_one_valid_word(self):
        words = ['users']

        candidates = self.completer.complete_next_word(words)

        self.command_registry.complete_next_word.assert_called_once_with(['users'])
        assert_that(candidates, equal_to(['agents', 'users']))

    def test_complete_last_word_two_valid_words(self):
        words = ['users', 'a']

        candidates = self.completer.complete_last_word(words)

        self.command_registry.complete_next_word.assert_called_once_with(['users'])
        assert_that(candidates, equal_to(['agents']))
