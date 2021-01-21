# -*- coding: utf-8 -*-
# Copyright 2014-2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import sys

DEFAULT_LOG_FORMAT = '%(asctime)s [%(process)d] (%(levelname)s) (%(name)s): %(message)s'
DEFAULT_LOG_LEVEL = logging.INFO


# This is fixed in Python 3.7.4 standard library, but Debian uses 3.7.3
# See https://github.com/python/cpython/commit/6a7a9f1d83cef628d2bacd71ee568b93f53fd6b4

class StreamHandler(logging.StreamHandler):

    def emit(self, record):
        try:
            super(StreamHandler, self).emit(record)
        except RecursionError:
            raise

    def handleError(self, record):
        try:
            super(StreamHandler, self).handleError(record)
        except RecursionError:
            raise


class FileHandler(StreamHandler, logging.FileHandler):
    pass


class _StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.

    Source: http://www.electricmonk.nl/log/2011/08/14/redirect-stdout-and-stderr-to-a-logger-in-python/
    Copyright 2011 by Ferry Boender
    SPDX-License-Identifier: GPL-2.0+
    """

    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        for handler in self.logger.handlers:
            handler.flush()

    def close(self):
        for handler in self.logger.handlers:
            handler.close()


class _LogLevelFilter(logging.Filter):
    def __init__(self, level_filter):
        self._level_filter = level_filter

    def filter(self, record):
        return self._level_filter(record.levelno)


def setup_logging(
    log_file,
    debug=False,
    log_level=DEFAULT_LOG_LEVEL,
    log_format=DEFAULT_LOG_FORMAT,
):
    """
    logger.*  ------------------------ v
    sys.stdout > streamtologger(INFO)  > logger > streamhandler(level<ERROR) > sys.stdout
    sys.stderr > streamtologger(ERROR) ^        > streamhandler(level>=ERROR) > sys.stderr
                                                > filehandler(all levels) > file
    """
    root_logger = logging.getLogger()

    formatter = logging.Formatter(log_format)

    handler = FileHandler(log_file)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    stdout_handler = StreamHandler(sys.stdout)
    stdout_handler.addFilter(_LogLevelFilter(lambda level: level < logging.ERROR))
    stdout_handler.setFormatter(formatter)
    root_logger.addHandler(stdout_handler)

    stderr_handler = StreamHandler(sys.stderr)
    stderr_handler.addFilter(_LogLevelFilter(lambda level: level >= logging.ERROR))
    stderr_handler.setFormatter(formatter)
    root_logger.addHandler(stderr_handler)

    if debug:
        log_level = logging.DEBUG
    root_logger.setLevel(log_level)

    sys.stdout = _StreamToLogger(logging.getLogger('STDOUT'), logging.INFO)
    sys.stderr = _StreamToLogger(logging.getLogger('STDERR'), logging.ERROR)

    sys.excepthook = excepthook


def silence_loggers(logger_names, level):
    for name in logger_names:
        logger = logging.getLogger(name)
        logger.setLevel(level)


def excepthook(exception_class, exception_instance, traceback):
    try:
        logging.getLogger().critical(
            exception_instance, exc_info=(exception_class, exception_instance, traceback)
        )
    except Exception:
        # If we get an exception here, it means that there was a problem with the logger
        # itself. Probably related to filesystem issues or formatting issues.
        sys.stderr = sys.__stderr__
        sys.stdout = sys.__stdout__
        logging.getLogger().critical(
            exception_instance, exc_info=(exception_class, exception_instance, traceback)
        )


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
