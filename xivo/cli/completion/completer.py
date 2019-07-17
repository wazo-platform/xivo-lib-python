# -*- coding: utf-8 -*-
# Copyright 2013-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later


class CommandLineCompleter(object):
    def __init__(self, command_registry):
        self._command_registry = command_registry

    def complete_last_word(self, words):
        last_word = words[-1]
        candidates = self._command_registry.complete_next_word(words[:-1])
        return sorted(
            candidate for candidate in candidates if candidate.startswith(last_word)
        )

    def complete_next_word(self, words):
        candidates = self._command_registry.complete_next_word(words)
        return sorted(candidates)
