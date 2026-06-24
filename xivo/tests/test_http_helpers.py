# Copyright 2016-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import json
import unittest
from unittest.mock import ANY, Mock, patch

from hamcrest import assert_that, equal_to, matches_regexp

from xivo.http_helpers import (
    BodyFormatter,
    LazyHeaderFormatter,
    _parse_traceparent,
    log_before_request,
    log_request,
    log_request_hide_token,
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
                '-',
                '-',
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
                '-',
                '-',
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
                '-',
                '-',
            )

    @patch('xivo.http_helpers.g', spec={})
    def test_log_before_request_sets_trace_id_from_traceparent_header(self, g):
        traceparent = '00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01'
        mock_request = Mock(data=b'', method='GET')
        mock_request.headers.get.side_effect = (
            lambda k, *a: traceparent if k == 'traceparent' else None
        )
        mock_request.url = '/foo/bar'

        with (
            patch('xivo.http_helpers.request', mock_request),
            patch('xivo.http_helpers.current_app', Mock()) as mock_current_app,
        ):
            log_before_request()

            assert_that(g.trace_id, equal_to('4bf92f3577b34da6a3ce929d0e0e4736'))
            assert_that(g.request_id, matches_regexp(r'^[0-9a-f]{16}$'))
            params = mock_current_app.logger.info.call_args[0][-1]
            assert_that(
                params['trace_id'], equal_to('4bf92f3577b34da6a3ce929d0e0e4736')
            )

    @patch('xivo.http_helpers.g', spec={})
    def test_log_before_request_falls_back_to_wazo_trace_id_header(self, g):
        wazo_trace_id = 'a06f7f341db5b95a-AMS'
        mock_request = Mock(data=b'', method='GET')
        mock_request.headers.get.side_effect = (
            lambda k, *a: wazo_trace_id if k == 'Wazo-Trace-ID' else None
        )
        mock_request.url = '/foo/bar'

        with (
            patch('xivo.http_helpers.request', mock_request),
            patch('xivo.http_helpers.current_app', Mock()) as mock_current_app,
        ):
            log_before_request()

            assert_that(g.trace_id, equal_to(wazo_trace_id))
            assert_that(g.request_id, matches_regexp(r'^[0-9a-f]{16}$'))
            params = mock_current_app.logger.info.call_args[0][-1]
            assert_that(params['trace_id'], equal_to(wazo_trace_id))

    @patch('xivo.http_helpers.g', spec={})
    def test_log_before_request_mints_trace_id_when_no_header(self, g):
        mock_request = Mock(data=b'', method='GET')
        mock_request.headers.get = Mock(return_value=None)
        mock_request.url = '/foo/bar'

        with (
            patch('xivo.http_helpers.request', mock_request),
            patch('xivo.http_helpers.current_app', Mock()) as mock_current_app,
        ):
            log_before_request()

            assert_that(g.request_id, matches_regexp(r'^[0-9a-f]{16}$'))
            assert_that(g.trace_id, matches_regexp(r'^[0-9a-f]{32}$'))
            params = mock_current_app.logger.info.call_args[0][-1]
            assert_that(params['request_id'], equal_to(g.request_id))
            assert_that(params['trace_id'], equal_to(g.trace_id))

    @patch('xivo.http_helpers.g', spec={})
    def test_log_before_request_percent_and_brace_in_trace_id_are_safe(self, g):
        trace_id = '100%complete{json}'
        mock_request = Mock(data=b'', method='GET')
        mock_request.headers.get.side_effect = (
            lambda k, *a: trace_id if k == 'Wazo-Trace-ID' else None
        )
        mock_request.url = '/foo/bar'

        with (
            patch('xivo.http_helpers.request', mock_request),
            patch('xivo.http_helpers.current_app', Mock()) as mock_current_app,
        ):
            log_before_request()

            assert_that(g.trace_id, equal_to(trace_id))
            params = mock_current_app.logger.info.call_args[0][-1]
            assert_that(params['trace_id'], equal_to(trace_id))

    @patch('xivo.http_helpers.g', spec={})
    def test_log_request_includes_request_id_and_trace_id(self, g):
        g.request_id = '0123456789abcdef'
        g.trace_id = '4bf92f3577b34da6a3ce929d0e0e4736'
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
                '0123456789abcdef',
                '4bf92f3577b34da6a3ce929d0e0e4736',
            )


class TestParseTraceparent(unittest.TestCase):
    def test_valid_traceparent_returns_trace_id(self):
        value = '00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01'
        assert_that(
            _parse_traceparent(value), equal_to('4bf92f3577b34da6a3ce929d0e0e4736')
        )

    def test_mixed_case_traceparent_is_lowercased(self):
        value = '00-4BF92F3577B34DA6A3CE929D0E0E4736-00F067AA0BA902B7-01'
        assert_that(
            _parse_traceparent(value), equal_to('4bf92f3577b34da6a3ce929d0e0e4736')
        )

    def test_none_returns_none(self):
        assert_that(_parse_traceparent(None), equal_to(None))

    def test_all_zero_trace_id_returns_none(self):
        value = '00-00000000000000000000000000000000-00f067aa0ba902b7-01'
        assert_that(_parse_traceparent(value), equal_to(None))

    def test_all_zero_parent_id_returns_none(self):
        value = '00-4bf92f3577b34da6a3ce929d0e0e4736-0000000000000000-01'
        assert_that(_parse_traceparent(value), equal_to(None))

    def test_invalid_version_ff_returns_none(self):
        value = 'ff-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01'
        assert_that(_parse_traceparent(value), equal_to(None))

    def test_malformed_returns_none(self):
        assert_that(_parse_traceparent('not-a-traceparent'), equal_to(None))
        assert_that(
            _parse_traceparent('00-tooshort-00f067aa0ba902b7-01'), equal_to(None)
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

    def test_valid_json_but_integer(self):
        body = b'1'

        formatter = BodyFormatter(body, hidden_fields=['four'])

        assert_that(f'{formatter}', equal_to('1'))

    def test_valid_json_but_string(self):
        body = b'"hello world"'

        formatter = BodyFormatter(body, None)

        assert_that(f'{formatter}', equal_to('"hello world"'))

    def test_valid_json_but_array(self):
        body = b'[1,2,3]'

        formatter = BodyFormatter(body, None)

        assert_that(f'{formatter}', equal_to('[1,2,3]'))


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
