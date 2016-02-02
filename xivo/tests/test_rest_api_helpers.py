# -*- coding: utf-8 -*-

# Copyright (C) 2016 Avencall
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


from hamcrest import assert_that
from hamcrest import contains
from hamcrest import equal_to
from hamcrest import has_entries
from hamcrest import instance_of
from hamcrest import is_
from hamcrest import raises
from mock import patch
from mock import sentinel as s
from unittest import TestCase

from ..rest_api_helpers import APIException
from ..rest_api_helpers import handle_api_exception


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

    def test_given_api_exception_when_handle_api_exception_then_return_formatted_response(self):

        @handle_api_exception
        def decorated():
            raise APIException(s.status_code,
                               s.message,
                               s.error_id,
                               s.details)

        result = decorated()

        assert_that(result, contains(
            has_entries({
                'message': s.message,
                'error_id': s.error_id,
                'details': s.details,
                'timestamp': instance_of(float)
            }),
            s.status_code))

    @patch('xivo.rest_api_helpers.logger')
    def test_given_api_exception_when_handle_api_exception_then_logs_error(self, logger):

        @handle_api_exception
        def decorated():
            raise APIException(s.status_code,
                               s.message,
                               s.error_id)

        decorated()

        assert_that(logger.error.called, is_(True))
