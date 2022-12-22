# Copyright 2014-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from unittest.mock import patch, sentinel
from xivo import daemonize


@patch('xivo.daemonize.unlock_pidfile')
@patch('xivo.daemonize.lock_pidfile_or_die')
class TestPidfileContext(unittest.TestCase):
    def test_that_lock_is_called(self, lock_fn, _unlock_fn):
        with daemonize.pidfile_context(sentinel.filename):
            lock_fn.assert_called_once_with(sentinel.filename)

    def test_that_unlock_is_called(self, _lock_fn, unlock_fn):
        with daemonize.pidfile_context(sentinel.filename):
            pass

        unlock_fn.assert_called_once_with(sentinel.filename)

    def test_that_unlock_is_called_on_exception(self, _lock_fn, unlock_fn):
        def f():
            with daemonize.pidfile_context(sentinel.filename):
                raise Exception('ok')

        self.assertRaises(Exception, f)

        unlock_fn.assert_called_once_with(sentinel.filename)
