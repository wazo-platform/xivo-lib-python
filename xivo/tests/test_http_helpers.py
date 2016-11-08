# -*- coding: utf-8 -*-
# Copyright 2016 Proformatique Inc.
# SPDX-License-Identifier: GPL-3.0+

import unittest

from mock import patch, sentinel, ANY

from xivo.http_helpers import log_request, log_request_hide_token


class TestLogRequest(unittest.TestCase):

    @patch('xivo.http_helpers.current_app')
    @patch('xivo.http_helpers.request')
    def test_log_request(self, request, current_app):
        request.url = '/foo/bar?token=1734768e-caf6'

        log_request(sentinel)

        current_app.logger.info.assert_called_once_with(
            ANY, request.remote_addr, request.method, request.url, sentinel.status_code)

    @patch('xivo.http_helpers.current_app')
    @patch('xivo.http_helpers.request')
    def test_log_request_hide_token(self, request, current_app):
        request.url = '/foo/bar?token=1734768e-caf6'

        log_request_hide_token(sentinel)

        expected_url = '/foo/bar?token=<hidden>'
        current_app.logger.info.assert_called_once_with(
            ANY, request.remote_addr, request.method, expected_url, sentinel.status_code)
