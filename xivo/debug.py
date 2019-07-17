# -*- coding: utf-8 -*-
# Copyright 2013-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import functools
import logging
import time
import os

logger = logging.getLogger(__name__)

DEBUG_MODE = os.environ.get('XIVO_DEBUG')


def _debug(decorator):
    if DEBUG_MODE:
        return decorator
    else:
        return _no_op_decorator


def _no_op_decorator(fun):
    return fun


@_debug
def trace_duration(fun):
    fun_name = fun.__name__

    @functools.wraps(fun)
    def aux(*args, **kwargs):
        start_time = time.time()
        result = fun(*args, **kwargs)
        duration = time.time() - start_time
        logger.info('Execution of %r took %.3fs', fun_name, duration)
        return result

    return aux


@_debug
def trace_call(fun):
    fun_name = fun.__name__

    @functools.wraps(fun)
    def aux(*args, **kwargs):
        logger.info('Executing %r', fun_name)
        result = fun(*args, **kwargs)
        return result

    return aux
