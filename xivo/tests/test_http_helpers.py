# Copyright 2016-2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import json
import unittest
from unittest.mock import ANY, Mock, patch

from hamcrest import assert_that, equal_to

from xivo.http_helpers import (
    BodyFormatter,
    LazyHeaderFormatter,
    log_request,
    log_request_hide_token,
    parse_content_disposition_filename,
    parse_content_type,
)


def _assert_json_equals(result, expected):
    serialized_result = json.loads(result)
    assert_that(serialized_result, equal_to(expected))


class TestLogRequest(unittest.TestCase):
    @patch('xivo.http_helpers.g', spec={})
    def test_log_request(self, g):
        del g.request_time
        mock_request = Mock()
        mock_request.url = '/foo/bar?token=1734768e-caf6'
        response = Mock(data=None, status_code=200)

        with (
            patch('xivo.http_helpers.request', mock_request),
            patch('xivo.http_helpers.current_app', Mock()) as mock_current_app,
        ):
            log_request(response)

            mock_current_app.logger.info.assert_called_once_with(
                ANY,
                mock_request.remote_addr,
                '',
                mock_request.method,
                mock_request.url,
                200,
            )

    @patch('xivo.http_helpers.g', spec={})
    def test_log_request_hide_token(self, g):
        del g.request_time
        mock_request = Mock()
        mock_request.url = '/foo/bar?token=1734768e-caf6'
        response = Mock(data=None, status_code=200)

        with (
            patch('xivo.http_helpers.request', mock_request),
            patch('xivo.http_helpers.current_app', Mock()) as mock_current_app,
        ):
            log_request_hide_token(response)

            expected_url = '/foo/bar?token=<hidden>'
            mock_current_app.logger.info.assert_called_once_with(
                ANY,
                mock_request.remote_addr,
                '',
                mock_request.method,
                expected_url,
                200,
            )

    @patch('xivo.http_helpers.g', spec={})
    def test_log_with_duration(self, g):
        g.request_time = 1667410149.0782132
        mock_request = Mock()
        mock_request.url = '/foo/bar'
        response = Mock(data=None, status_code=200)

        with (
            patch('xivo.http_helpers.request', mock_request),
            patch('xivo.http_helpers.current_app', Mock()) as mock_current_app,
        ):
            log_request(response)

            mock_current_app.logger.info.assert_called_once_with(
                ANY,
                mock_request.remote_addr,
                ANY,
                mock_request.method,
                mock_request.url,
                200,
            )


class TestBodyFormatter(unittest.TestCase):
    def test_valid_json_body_no_hidden_field(self):
        body = b'{"one": 1, "two": 2, "three": 3}'

        formatter = BodyFormatter(body, hidden_fields=None)

        _assert_json_equals(f'{formatter}', {'one': 1, 'two': 2, 'three': 3})

    def test_valid_json_body_with_hidden_field(self):
        body = b'{"one": 1, "two": 2, "three": 3}'

        formatter = BodyFormatter(body, hidden_fields=['two'])

        _assert_json_equals(f'{formatter}', {'one': 1, 'two': '<hidden>', 'three': 3})

    def test_invalid_json_body_with_hidden_field(self):
        body = b'{"one": 1, "two": 2, "three": 3,}'  # See that trialing coma

        formatter = BodyFormatter(body, hidden_fields=['two'])

        assert_that(f'{formatter}', equal_to('<hidden>'))

    def test_invalid_json_body_with_hidden_field_no_match(self):
        body = b'{"one": 1, "two": 2, "three": 3,}'  # See that trialing coma

        formatter = BodyFormatter(body, hidden_fields=['four'])

        assert_that(f'{formatter}', equal_to('{"one": 1, "two": 2, "three": 3,}'))


class TestHeaderFormatter(unittest.TestCase):
    def test_that_tokens_are_partially_masked(self):
        raw = {'X-Auth-Token': '87916129-1897-408c-a12f-bc629ca6c480'}
        formatter = LazyHeaderFormatter(raw)

        assert_that(
            f'{formatter}',
            equal_to("{'X-Auth-Token': 'XXXXXXXX-XXXX-XXXX-XXXX-XXXX9ca6c480'}"),
        )

    def test_that_basic_authorization_is_masked(self):
        raw = {'Authorization': 'Basic cm9vdDpzdXBlcn1233M='}
        formatter = LazyHeaderFormatter(raw)

        assert_that(f'{formatter}', equal_to("{'Authorization': 'Basic <hidden>'}"))

    def test_that_all_other_authorization_are_completely_masked(self):
        raw = {'Authorization': 'unknown'}
        formatter = LazyHeaderFormatter(raw)

        assert_that(f'{formatter}', equal_to("{'Authorization': '<hidden>'}"))


class TestParseContentDispositionFilename(unittest.TestCase):
    CONTENT_DISPOSITION_FILENAMES = [
        ('inline', None),
        ('attachment', None),
        ('attachment; filename="file name.jpg"', 'file name.jpg'),
        ('attachment; filename*=UTF-8\'\'file%20name.jpg', 'file name.jpg'),
    ]

    def test_parse_content_disposition_filename(self):
        for header, expected_filename in self.CONTENT_DISPOSITION_FILENAMES:
            filename = parse_content_disposition_filename(header)
            assert filename == expected_filename


class TestParseContentType(unittest.TestCase):
    CONTENT_TYPES = [
        (
            'text/html; charset=utf-8',
            ('text/html', {'charset': 'utf-8'}),
        ),
        (
            'multipart/form-data; boundary=ExampleBoundaryString',
            ('multipart/form-data', {'boundary': 'ExampleBoundaryString'}),
        ),
    ]

    def test_parse_content_type(self):
        for header, (expected_content_type, expected_params) in self.CONTENT_TYPES:
            content_type, params = parse_content_type(header)
            assert content_type == expected_content_type
            assert params == expected_params
