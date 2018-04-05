# -*- coding: utf-8 -*-
# Copyright (C) 2013-2014 Avencall
# SPDX-License-Identifier: GPL-3.0+


class CommandLine(object):

    def __init__(self, words, command, command_args):
        self.words = words
        self.command = command
        self.command_args = command_args

    def is_blank(self):
        return not self.words
