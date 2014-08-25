# -*- coding: utf-8 -*-

# Copyright (C) 2014 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import unittest

from mock import patch
from mock import Mock
from mock import sentinel
from xivo import daemonize


@patch('xivo.daemonize.daemonize', Mock())
@patch('xivo.daemonize.unlock_pidfile')
@patch('xivo.daemonize.lock_pidfile_or_die')
class TestPidfileContext(unittest.TestCase):

    def test_that_lock_is_called(self, lock_fn, _unlock_fn):
        with daemonize.pidfile_context(sentinel.filename):
            lock_fn.assert_called_once_with(sentinel.filename)

    def test_that_unlock_is_called(self, lock_fn, unlock_fn):
        with daemonize.pidfile_context(sentinel.filename):
            pass

        unlock_fn.assert_called_once_with(sentinel.filename)

    def test_that_unlock_is_called_on_exception(self, lock_fn, unlock_fn):
        def f():
            with daemonize.pidfile_context(sentinel.filename):
                raise Exception('ok')

        self.assertRaises(Exception, f)

        unlock_fn.assert_called_once_with(sentinel.filename)
