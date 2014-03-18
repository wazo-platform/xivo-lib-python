# -*- coding: utf-8 -*-

# Copyright (C) 2013-2014 Avencall
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
