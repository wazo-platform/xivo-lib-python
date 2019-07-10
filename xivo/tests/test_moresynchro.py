# -*- coding: utf-8 -*-
# Copyright 2014-2019 The Wazo Authors  (see the AUTHORS file)
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
