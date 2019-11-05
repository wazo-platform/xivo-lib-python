# -*- coding: utf-8 -*-
# Copyright 2016-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from unittest import TestCase

from hamcrest import (
    assert_that,
    contains,
    equal_to,
    has_entries,
    instance_of,
    is_,
    raises,
)
from mock import patch, sentinel as s

from ..rest_api_helpers import APIException, handle_api_exception


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
            contains(
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
            contains(
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
