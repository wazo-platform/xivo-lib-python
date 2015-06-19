# -*- coding: utf-8 -*-

# Copyright (C) 2014-2015 Avencall
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

from cStringIO import StringIO
import logging
import sys
import tempfile
from unittest import TestCase

from hamcrest import assert_that
from hamcrest import contains_string
from hamcrest import equal_to
from hamcrest import has_length
from hamcrest import is_
from hamcrest import is_not
from mock import Mock, patch

from xivo.xivo_logging import DEFAULT_LOG_FORMAT
from xivo.xivo_logging import DEFAULT_LOG_LEVEL
from xivo.xivo_logging import excepthook
from xivo.xivo_logging import get_log_level_by_name
from xivo.xivo_logging import setup_logging


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

        stream_handler.setFormatter.assert_any_call(formatter)
        root_logger.addHandler.assert_any_call(stream_handler)

    def test_setup_logging_with_no_flags_then_log_level_is_default(self, logging):
        log_file = Mock()
        root_logger = logging.getLogger.return_value

        setup_logging(log_file)

        root_logger.setLevel.assert_called_once_with(DEFAULT_LOG_LEVEL)

    def test_setup_logging_with_debug_then_log_level_is_debug(self, logging):
        log_file = Mock()
        root_logger = logging.getLogger.return_value

        setup_logging(log_file, debug=True)

        root_logger.setLevel.assert_called_once_with(logging.DEBUG)

    def test_setup_logging_with_loglevel_then_log_level_is_changed(self, logging):
        log_file = Mock()
        root_logger = logging.getLogger.return_value

        setup_logging(log_file, log_level=logging.ERROR)

        root_logger.setLevel.assert_called_once_with(logging.ERROR)

    def test_setup_logging_with_loglevel_and_debug_then_log_level_is_debug(self, logging):
        log_file = Mock()
        root_logger = logging.getLogger.return_value

        setup_logging(log_file, debug=True, log_level=logging.ERROR)

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

    def test_that_setup_logging_adds_excepthook(self, logging):
        log_file = Mock()

        with patch('sys.excepthook') as new_hook:
            setup_logging(log_file)

            assert_that(sys.excepthook, is_not(new_hook))
            assert_that(sys.excepthook, is_(excepthook))


@patch('sys.stderr', new_callable=StringIO)
@patch('sys.stdout', new_callable=StringIO)
class TestLoggingOutput(TestCase):
    def setUp(self):
        _, self.file_name = tempfile.mkstemp()

    def test_setup_logging_when_log_in_info_level_then_log_in_stdout(self, stdout, stderr):
        message = 'test info'

        setup_logging(self.file_name, foreground=True)
        logging.getLogger('test').info(message)

        assert_that(stdout.getvalue(), contains_string(message))
        assert_that(stderr.getvalue(), has_length(0))

    def test_setup_logging_when_log_in_warning_level_then_log_in_stdout(self, stdout, stderr):
        message = ''

        setup_logging(self.file_name, foreground=True)
        logging.getLogger('test').warning(message)

        assert_that(stdout.getvalue(), contains_string(message))
        assert_that(stderr.getvalue(), '')

    def test_setup_logging_when_log_in_error_level_then_log_in_stderr(self, stdout, stderr):
        message = 'test error'
        _, file_name = tempfile.mkstemp()

        setup_logging(file_name, foreground=True)
        logging.getLogger('test').error(message)

        assert_that(stderr.getvalue(), contains_string(message))
        assert_that(stdout.getvalue(), has_length(0))


class TestLogLevelByName(TestCase):

    def test_get_log_level_by_name_when_unknown_then_raise_valueerror(self):
        self.assertRaises(ValueError, get_log_level_by_name, 'not a log level name')

    def test_get_log_level_by_name_when_valid_name_then_return_log_level(self):
        assert_that(get_log_level_by_name('DEBUG'), equal_to(logging.DEBUG))
        assert_that(get_log_level_by_name('INFO'), equal_to(logging.INFO))
        assert_that(get_log_level_by_name('WARNING'), equal_to(logging.WARNING))
        assert_that(get_log_level_by_name('ERROR'), equal_to(logging.ERROR))
        assert_that(get_log_level_by_name('CRITICAL'), equal_to(logging.CRITICAL))

    def test_get_log_level_by_name_when_valid_lower_name_then_return_log_level(self):
        assert_that(get_log_level_by_name('debug'), equal_to(logging.DEBUG))
        assert_that(get_log_level_by_name('info'), equal_to(logging.INFO))
        assert_that(get_log_level_by_name('warning'), equal_to(logging.WARNING))
        assert_that(get_log_level_by_name('error'), equal_to(logging.ERROR))
        assert_that(get_log_level_by_name('critical'), equal_to(logging.CRITICAL))
