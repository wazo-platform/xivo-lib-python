# -*- coding: utf-8 -*-

# Copyright (C) 2013-2014 Avencall
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

import errno

from mock import Mock, patch
from unittest import TestCase
from xivo import pid_file


class TestPIDFile(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @patch('os.unlink', Mock(side_effect=OSError(errno.ENOENT, 'msg')))
    def test_remove_pid_file_no_such_file_no_error(self):
        pid_file.remove_pid_file('/foo/bar')

    @patch('os.unlink', Mock(side_effect=OSError(errno.EACCES, 'msg')))
    def test_remove_pid_file_other_errno(self):
        self.assertRaises(OSError, pid_file.remove_pid_file, '/foo/bar')
