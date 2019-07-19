# -*- coding: utf-8 -*-
# Copyright 2016-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from hamcrest import (
    assert_that,
    equal_to,
    has_entries,
)

from xivo.http_json_server import (
    HttpReqHandler
)


class FakeHttpReqHandler(HttpReqHandler):
    def __init__(self):
        pass


class TestHttpJsonServer(unittest.TestCase):

    def test_pathtify(self):
        partial_uri = '/awesome/path/file.ext?foo=bar&foo=fish&other=what#anchor'
        req_handler = FakeHttpReqHandler()
        req_handler.path = partial_uri
        path, query_string, fragment = req_handler.pathify()
        assert_that(path, equal_to('/awesome/path/file.ext'))
        assert_that(query_string, has_entries(
            # Should be foo=['bar', 'fish'], but the legacy version was not rfc
            # compliant so we stay not compliant...
            foo='fish',
            other="what"
        ))
        assert_that(fragment, equal_to('anchor'))
