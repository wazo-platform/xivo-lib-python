# Copyright 2014-2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging
import sys
import types
from collections.abc import Callable, Sequence

DEFAULT_LOG_FORMAT = '%(asctime)s [%(process)d] (%(levelname)s) (%(name)s): %(message)s'
DEFAULT_LOG_LEVEL = logging.INFO


class _StreamToLogger:
    """
    Fake file-like stream object that redirects writes to a logger instance.

    Source: http://www.electricmonk.nl/log/2011/08/14/redirect-stdout-and-stderr-to-a-logger-in-python/  # noqa: E501
    Copyright 2011 by Ferry Boender
    SPDX-License-Identifier: GPL-2.0+
    """

    def __init__(self, logger: logging.Logger, log_level: int = logging.INFO) -> None:
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf: str) -> None:
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self) -> None:
        for handler in self.logger.handlers:
            handler.flush()

    def close(self) -> None:
        for handler in self.logger.handlers:
            handler.close()


class _LogLevelFilter(logging.Filter):
    def __init__(self, level_filter: Callable[[int], bool]) -> None:
        self._level_filter = level_filter

    def filter(self, record: logging.LogRecord) -> bool:
        return self._level_filter(record.levelno)


def setup_logging(
    log_file: str,
    debug: bool = False,
    log_level: int = DEFAULT_LOG_LEVEL,
    log_format: str = DEFAULT_LOG_FORMAT,
) -> None:
    """
    logger.*  ------------------------ v
    sys.stdout > streamtologger(INFO)  > logger > streamhandler(level<ERROR) > sys.stdout
    sys.stderr > streamtologger(ERROR) ^        > streamhandler(level>=ERROR) > sys.stderr
                                                > filehandler(all levels) > file
    """
    root_logger = logging.getLogger()

    formatter = logging.Formatter(log_format)

    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.addFilter(_LogLevelFilter(lambda level: level < logging.ERROR))
    stdout_handler.setFormatter(formatter)
    root_logger.addHandler(stdout_handler)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.addFilter(_LogLevelFilter(lambda level: level >= logging.ERROR))
    stderr_handler.setFormatter(formatter)
    root_logger.addHandler(stderr_handler)

    if debug:
        log_level = logging.DEBUG
    root_logger.setLevel(log_level)

    sys.stdout = _StreamToLogger(logging.getLogger('STDOUT'), logging.INFO)
    sys.stderr = _StreamToLogger(logging.getLogger('STDERR'), logging.ERROR)

    sys.excepthook = excepthook


def silence_loggers(logger_names: Sequence[str], level: int) -> None:
    for name in logger_names:
        logger = logging.getLogger(name)
        logger.setLevel(level)


def excepthook(
    exception_class: type[BaseException],
    exception_instance: BaseException,
    traceback: types.TracebackType | None,
) -> None:
    logging.getLogger().critical(
        exception_instance, exc_info=(exception_class, exception_instance, traceback)
    )


def get_log_level_by_name(log_level_name: str) -> int:
    levels = {
        'CRITICAL': logging.CRITICAL,
        'ERROR': logging.ERROR,
        'WARNING': logging.WARNING,
        'INFO': logging.INFO,
        'DEBUG': logging.DEBUG,
    }
    log_level_name = log_level_name.upper()

    if log_level_name not in levels:
        raise ValueError(f'Unknown log level {log_level_name}')

    return levels[log_level_name]
