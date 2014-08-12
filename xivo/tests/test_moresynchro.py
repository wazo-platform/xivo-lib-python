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

from mock import Mock
from unittest import TestCase
from xivo import moresynchro


class TestOnce(TestCase):
    
    def test_once_no_concurrency(self):
        once = moresynchro.Once()
        init_routine = Mock()
        
        once.once(init_routine)
        once.once(init_routine)
        
        init_routine.assert_called_once_with()
