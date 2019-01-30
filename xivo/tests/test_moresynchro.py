# -*- coding: utf-8 -*-
# Copyright (C) 2014 Avencall
# SPDX-License-Identifier: GPL-3.0-or-later

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
