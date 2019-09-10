# -*- coding: utf-8 -*-
# Copyright 2013-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from xivo import xivo_helpers


class TestXivoHelpers(unittest.TestCase):

    PREFIX = '_*735.'

    def test_fkey_extension_unc_fwd_with_destination(self):
        arguments = ('123', '_*21.', '1002')

        result = xivo_helpers.fkey_extension(self.PREFIX, arguments)

        self.assertEqual(result, '*735123***221*1002')

    def test_fkey_extension_unc_fwd_without_destination(self):
        arguments = ('123', '_*21.', '')

        result = xivo_helpers.fkey_extension(self.PREFIX, arguments)

        self.assertEqual(result, '*735123***221')

    def test_fkey_extension_dnd(self):
        arguments = ('123', '*25', '')

        result = xivo_helpers.fkey_extension(self.PREFIX, arguments)

        self.assertEqual(result, '*735123***225')


class TestPositionOfAsteriskPatternChar(unittest.TestCase):
    def test_position_of_asterisk_pattern_char(self):
        samples = [
            ('_418[1-5]XZ123', 4),
            ('418-123-5599', None),
            ('_NXXXXXXXXXX', 1),
            ('NXXXXXXXXXX', 0),
            ('_1XXXXXXXXXX', 2),
        ]

        for pattern, expected in samples:
            result = xivo_helpers.position_of_asterisk_pattern_char(pattern)
            self.assertEqual(result, expected)
