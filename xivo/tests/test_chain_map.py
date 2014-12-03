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

import operator
import unittest

from ..chain_map import ChainMap
from hamcrest import assert_that
from hamcrest import equal_to
from hamcrest import is_
from hamcrest import none


class TestChainMap(unittest.TestCase):

    def test_access_no_result(self):
        m = ChainMap({}, {})

        self.assertRaises(KeyError, operator.getitem, m, 'key')
        assert_that(m.get('key'), is_(none()))
        assert_that(m.get('key', 'default_value'), equal_to('default_value'))

    def test_lookup_order(self):
        cli_config = {}
        environment_config = {'key': 2}
        file_config = {'key': 3,
                       'test': 42}
        default_config = {'key': 4}

        m = ChainMap(cli_config, environment_config, file_config, default_config)

        assert_that(m['key'], equal_to(2))
        assert_that(m['test'], equal_to(42))

    def test_get_item_with_none_value(self):
        m = ChainMap({'a': None})

        assert_that(m['a'] is None)
