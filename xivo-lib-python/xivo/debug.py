# -*- coding: UTF-8 -*-

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
    def aux_fun(*args, **kwargs):
        start_time = time.time()
        result = fun(*args, **kwargs)
        duration = time.time() - start_time
        logger.info('Execution of %r took %.3fs', fun_name, duration)
        return result
    return aux_fun
