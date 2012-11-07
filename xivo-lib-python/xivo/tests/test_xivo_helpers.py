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
