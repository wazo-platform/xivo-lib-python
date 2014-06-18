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

from hamcrest import assert_that, equal_to
from mock import Mock, patch
from unittest import TestCase

from ..xivo_logging import DEFAULT_LOG_FORMAT, setup_logging


@patch('xivo.xivo_logging.logging')
class TestLogging(TestCase):

    def test_setup_logging_with_log_file_then_setup_logging_in_log_file(self, logging):
        log_file = 'my_log_file.log'
        root_logger = logging.getLogger.return_value
        file_handler = logging.FileHandler.return_value
        formatter = logging.Formatter.return_value

        setup_logging(log_file)

        logging.FileHandler.assert_called_once_with(log_file)
        file_handler.setFormatter.assert_called_once_with(formatter)
        root_logger.addHandler.assert_called_once_with(file_handler)

    def test_setup_logging_with_no_foreground_then_no_stream_logging(self, logging):
        log_file = Mock()

        setup_logging(log_file)

        assert_that(logging.StreamHandler.call_count, equal_to(0))

    def test_setup_logging_with_foreground_then_stream_logging(self, logging):
        log_file = Mock()
        root_logger = logging.getLogger.return_value
        stream_handler = logging.StreamHandler.return_value
        formatter = logging.Formatter.return_value

        setup_logging(log_file, foreground=True)

        stream_handler.setFormatter.assert_called_once_with(formatter)
        root_logger.addHandler.assert_any_call(stream_handler)

    def test_setup_logging_with_no_debug_then_log_level_is_info(self, logging):
        log_file = Mock()
        root_logger = logging.getLogger.return_value

        setup_logging(log_file)

        root_logger.setLevel.assert_called_once_with(logging.INFO)

    def test_setup_logging_with_debug_then_log_level_is_debug(self, logging):
        log_file = Mock()
        root_logger = logging.getLogger.return_value

        setup_logging(log_file, debug=True)

        root_logger.setLevel.assert_called_once_with(logging.DEBUG)

    def test_setup_logging_with_no_format_then_log_format_is_default(self, logging):
        log_file = Mock()

        setup_logging(log_file)

        logging.Formatter.assert_called_once_with(DEFAULT_LOG_FORMAT)

    def test_setup_logging_with_format_then_log_format_is_not_default(self, logging):
        log_file = Mock()
        log_format = Mock()

        setup_logging(log_file, log_format=log_format)

        logging.Formatter.assert_called_once_with(log_format)
