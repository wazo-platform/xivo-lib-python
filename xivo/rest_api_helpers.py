# -*- coding: utf-8 -*-
# Copyright 2016-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import time
import yaml

from functools import wraps
from pkg_resources import resource_string, iter_entry_points

logger = logging.getLogger(__name__)


class APIException(Exception):

    def __init__(self, status_code, message, error_id, details=None, resource=None):
        self.status_code = status_code
        self.message = message
        self.id_ = error_id
        self.details = details or {}
        self.resource = resource


def handle_api_exception(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIException as error:
            response = {
                'message': error.message,
                'error_id': error.id_,
                'details': error.details,
                'timestamp': time.time()
            }
            if error.resource:
                response['resource'] = error.resource
            logger.error('%s: %s', error.message, error.details)
            return response, error.status_code
    return wrapper


def load_all_api_specs(entry_point_group, spec_filename):
    for module in iter_entry_points(group=entry_point_group):
        try:
            spec = yaml.safe_load(resource_string(module.module_name, spec_filename))
            yield spec
        except IOError:
            logger.debug('API spec for module "%s" does not exist', module.module_name)
        except ImportError:
            logger.warning('Could not load module %s', module.module_name)
