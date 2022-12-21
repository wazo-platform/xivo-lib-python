# Copyright 2021-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from unittest import TestCase

from ..dialaction import (
    action,
    action_type,
    action_subtype,
)


class TestDialaction(TestCase):
    def test_action(self):
        assert action(None) == ''
        assert action('mytype') == 'mytype'
        assert action('mytype', 'mysubtype') == 'mytype:mysubtype'

    def test_action_type(self):
        assert action_type(None) is None
        assert action_type('mytype') == 'mytype'
        assert action_type('mytype:mysubtype') == 'mytype'
        assert action_type('mytype:mysubtype:suffix') == 'mytype'

    def test_action_subtype(self):
        assert action_subtype(None) is None
        assert action_subtype('mytype') is None
        assert action_subtype('mytype:mysubtype') == 'mysubtype'
        assert action_subtype('mytype:mysubtype:suffix') == 'mysubtype:suffix'
