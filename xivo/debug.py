# Copyright 2013-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import functools
import logging
import os
import time
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

DEBUG_MODE = os.environ.get('XIVO_DEBUG')


F = TypeVar('F', bound=Callable[..., Any])
R = TypeVar('R')


def _debug(decorator: Callable[[F], F]) -> F | Callable[[F], F]:
    if DEBUG_MODE:
        return decorator
    return _no_op_decorator


def _no_op_decorator(fun: F) -> F:
    return fun


@_debug
def trace_duration(fun: Callable[..., R]) -> Callable[..., R]:
    fun_name = fun.__name__

    @functools.wraps(fun)
    def aux(*args: Any, **kwargs: Any) -> R:
        start_time = time.time()
        result = fun(*args, **kwargs)
        duration = time.time() - start_time
        logger.info('Execution of %r took %.3fs', fun_name, duration)
        return result

    return aux


@_debug
def trace_call(fun: Callable[..., R]) -> Callable[..., R]:
    fun_name = fun.__name__

    @functools.wraps(fun)
    def aux(*args: Any, **kwargs: Any) -> R:
        logger.info('Executing %r', fun_name)
        result = fun(*args, **kwargs)
        return result

    return aux
