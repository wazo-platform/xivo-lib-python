# Copyright 2016-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from importlib.metadata import EntryPoint
from unittest import TestCase
from unittest.mock import create_autospec, patch
from unittest.mock import sentinel as s

from hamcrest import (
    assert_that,
    contains_exactly,
    empty,
    equal_to,
    has_entries,
    instance_of,
    is_,
    raises,
)

from ..rest_api_helpers import APIException, handle_api_exception, load_all_api_specs


class TestRestApiHelpers(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_given_no_exception_when_handle_api_exception_then_return_result(self):
        @handle_api_exception
        def decorated():
            return 'my', 'result'

        result = decorated()

        assert_that(result, equal_to(('my', 'result')))

    def test_given_unknown_exception_when_handle_api_exception_then_raise(self):
        @handle_api_exception
        def decorated():
            raise TypeError('test')

        assert_that(decorated, raises(TypeError))

    def test_given_api_exception_when_handle_api_exception_then_return_formatted_response(
        self,
    ):
        @handle_api_exception
        def decorated():
            raise APIException(s.status_code, s.message, s.error_id, s.details)

        result = decorated()

        assert_that(
            result,
            contains_exactly(
                has_entries(
                    {
                        'message': s.message,
                        'error_id': s.error_id,
                        'details': s.details,
                        'timestamp': instance_of(float),
                    }
                ),
                s.status_code,
            ),
        )

    def test_given_api_exception_with_a_resource(self):
        @handle_api_exception
        def decorated():
            raise APIException(
                s.status_code, s.message, s.error_id, s.details, resource=s.resource
            )

        result = decorated()

        assert_that(
            result,
            contains_exactly(
                has_entries(
                    {
                        'resource': s.resource,
                        'message': s.message,
                        'error_id': s.error_id,
                        'details': s.details,
                        'timestamp': instance_of(float),
                    }
                ),
                s.status_code,
            ),
        )

    @patch('xivo.rest_api_helpers.logger')
    def test_given_api_exception_when_handle_api_exception_then_logs_error(
        self, logger
    ):
        @handle_api_exception
        def decorated():
            raise APIException(s.status_code, s.message, s.error_id)

        decorated()

        assert_that(logger.error.called, is_(True))


def _make_entry_point(value):
    return create_autospec(spec=EntryPoint, value=value)


@patch('xivo.rest_api_helpers.importlib.resources.files')
@patch('xivo.rest_api_helpers.entry_points')
class TestLoadAllApiSpecs(TestCase):
    def _set_spec_content(self, resources_files, content):
        resources_files.return_value.joinpath.return_value.read_bytes.return_value = (
            content
        )

    def test_yields_parsed_specs(self, entry_points, resources_files):
        entry_points.return_value = [
            _make_entry_point('my_pkg.plugins.foo.http:ViewPlugin')
        ]
        self._set_spec_content(resources_files, b'info:\n  title: test')

        result = list(load_all_api_specs('my_group', 'api.yml'))

        assert_that(
            result,
            contains_exactly(has_entries(info=has_entries(title='test'))),
        )

    def test_package_name_derivation(self, entry_points, resources_files):
        cases = [
            ('wazo_dird.plugins.api.http:ApiViewPlugin', 'wazo_dird.plugins.api'),
            ('my_pkg.module:Class', 'my_pkg'),
            ('a.b.c.d.e:F', 'a.b.c.d'),
        ]
        for ep_value, expected_package in cases:
            resources_files.reset_mock()
            entry_points.return_value = [_make_entry_point(ep_value)]
            self._set_spec_content(resources_files, b'info: {}')

            list(load_all_api_specs('group', 'api.yml'))

            resources_files.assert_called_with(expected_package)

    def test_skips_missing_spec_file(self, entry_points, resources_files):
        entry_points.return_value = [
            _make_entry_point('my_pkg.plugins.foo.http:Plugin')
        ]
        resources_files.return_value.joinpath.return_value.read_bytes.side_effect = (
            OSError('file not found')
        )

        result = list(load_all_api_specs('group', 'api.yml'))

        assert_that(result, is_(empty()))

    def test_skips_unloadable_package(self, entry_points, resources_files):
        entry_points.return_value = [
            _make_entry_point('bad_pkg.plugins.foo.http:Plugin')
        ]
        resources_files.side_effect = ImportError('no module')

        result = list(load_all_api_specs('group', 'api.yml'))

        assert_that(result, is_(empty()))

    def test_empty_group(self, entry_points, resources_files):
        entry_points.return_value = []

        result = list(load_all_api_specs('group', 'api.yml'))

        assert_that(result, is_(empty()))
