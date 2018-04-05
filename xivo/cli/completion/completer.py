# -*- coding: utf-8 -*-
# Copyright (C) 2013-2014 Avencall
# SPDX-License-Identifier: GPL-3.0+


class CommandLineCompleter(object):

    def __init__(self, command_registry):
        self._command_registry = command_registry

    def complete_last_word(self, words):
        last_word = words[-1]
        candidates = self._command_registry.complete_next_word(words[:-1])
        return sorted(candidate for candidate in candidates if candidate.startswith(last_word))

    def complete_next_word(self, words):
        candidates = self._command_registry.complete_next_word(words)
        return sorted(candidates)
