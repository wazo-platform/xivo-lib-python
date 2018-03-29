# -*- coding: utf-8 -*-
# Copyright 2013-2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from __future__ import print_function
from __future__ import unicode_literals

import six


class InputRawCommandLineSource(object):

    def __init__(self, prompt):
        self._prompt = prompt

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            try:
                raw_command_line = six.b(six.moves.input(self._prompt)).decode('UTF-8')
                return raw_command_line
            except EOFError:
                print()
                raise StopIteration()
            except KeyboardInterrupt:
                print('^C')

    next = __next__
