# Copyright 2013-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later


class InputRawCommandLineSource:
    def __init__(self, prompt):
        self._prompt = prompt

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            try:
                raw_command_line = input(self._prompt)
                return raw_command_line
            except EOFError:
                print()
                raise StopIteration()
            except KeyboardInterrupt:
                print('^C')

    next = __next__
