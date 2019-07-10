# -*- coding: utf-8 -*-
# Copyright 2013-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later


class CommandLine(object):
    def __init__(self, words, command, command_args):
        self.words = words
        self.command = command
        self.command_args = command_args

    def is_blank(self):
        return not self.words
