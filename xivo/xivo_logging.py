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

import logging
import sys

DEFAULT_LOG_FORMAT = '%(asctime)s [%(process)d] (%(levelname)s) (%(name)s): %(message)s'
DEFAULT_LOG_LEVEL = logging.INFO


class _LogLevelFilter(logging.Filter):
    def __init__(self, level_filter):
        self._level_filter = level_filter

    def filter(self, record):
        return self._level_filter(record.levelno)


def setup_logging(log_file, foreground=False, debug=False, log_level=DEFAULT_LOG_LEVEL, log_format=DEFAULT_LOG_FORMAT):
    root_logger = logging.getLogger()

    formatter = logging.Formatter(log_format)

    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    if foreground:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.addFilter(_LogLevelFilter(lambda level: level <= log_level))
        stdout_handler.setFormatter(formatter)
        root_logger.addHandler(stdout_handler)

        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.addFilter(_LogLevelFilter(lambda level: level > log_level))
        stderr_handler.setFormatter(formatter)
        root_logger.addHandler(stderr_handler)

    if debug:
        log_level = logging.DEBUG
    root_logger.setLevel(log_level)


def get_log_level_by_name(log_level_name):
    levels = {
        'CRITICAL': logging.CRITICAL,
        'ERROR': logging.ERROR,
        'WARNING': logging.WARNING,
        'INFO': logging.INFO,
        'DEBUG': logging.DEBUG,
    }
    log_level_name = log_level_name.upper()

    if log_level_name not in levels:
        raise ValueError('Unknown log level {}'.format(log_level_name))

    return levels[log_level_name]
