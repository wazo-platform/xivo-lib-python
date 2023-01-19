# Copyright 2014-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import operator
import unittest

from ..chain_map import AccumulatingListChainMap as ALChainMap, ChainMap
from hamcrest import assert_that
from hamcrest import equal_to
from hamcrest import has_entry
from hamcrest import is_
from hamcrest import none


class TestChainMap(unittest.TestCase):
    def test_access_no_result(self):
        m = ChainMap({}, {})

        self.assertRaises(KeyError, operator.getitem, m, 'key')
        assert_that(m.get('key'), is_(none()))
        assert_that(m.get('key', 'default_value'), equal_to('default_value'))

    def test_lookup_order(self):
        cli_config: dict[str, int] = {}
        environment_config = {'key': 2}
        file_config = {'key': 3, 'test': 42}
        default_config = {'key': 4}

        m = ChainMap(cli_config, environment_config, file_config, default_config)

        assert_that(m['key'], equal_to(2))
        assert_that(m['test'], equal_to(42))

    def test_get_item_with_none_value(self):
        m = ChainMap({'a': None})

        assert_that(m['a'] is None)

    def test_overriding_nested_field(self):
        default_config = {
            'key': {
                'host': 'localhost',
                'port': 1234,
                'username': 'admin',
                'password': 'secret',
            }
        }
        file_config = {'key': {'host': 'other-host', 'password': 'not-secret'}}
        cli_config = {'key': {'host': 'test-host'}}

        m = ChainMap(cli_config, file_config, default_config)

        expected = {
            'key': {
                'host': 'test-host',
                'port': 1234,
                'username': 'admin',
                'password': 'not-secret',
            }
        }

        assert_that(m, equal_to(expected))
        assert_that(cli_config, equal_to({'key': {'host': 'test-host'}}))

    def test_overriding_none_with_dict_gives_none(self):
        original = {'key': None}
        new_dict = {'key': {'subkey': 'value'}}

        m = ChainMap(original, new_dict)

        assert_that(m, has_entry('key', None))


class TestAccumulatingListChainMap(unittest.TestCase):
    def test_list_is_accumulated(self):
        empty: dict[str, list[str]] = {}
        empty_list: dict[str, list] = {'key': []}
        one_item = {'key': ['item']}
        two_items = {'key': ['items', 'items']}

        assert ALChainMap(empty_list)['key'] == []

        try:
            ALChainMap(empty, empty)['key']
        except KeyError:
            assert True
        else:
            assert False

        assert ALChainMap(empty, empty_list)['key'] == []
        assert ALChainMap(empty_list, empty_list)['key'] == []
        assert ALChainMap(empty_list, one_item)['key'] == ['item']
        assert ALChainMap(one_item, one_item)['key'] == ['item', 'item']
        assert ALChainMap(empty, two_items)['key'] == ['items', 'items']
        assert ALChainMap(one_item, two_items)['key'] == ['item', 'items', 'items']
        assert ALChainMap(two_items, two_items)['key'] == ['items'] * 4
