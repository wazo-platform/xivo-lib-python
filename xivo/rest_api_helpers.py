# Copyright 2016-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import logging
import time
from functools import wraps
from typing import Any, Callable, TypeVar
from collections.abc import Generator

import yaml
from pkg_resources import iter_entry_points, resource_string

logger = logging.getLogger(__name__)

R = TypeVar('R')


class APIException(Exception):
    def __init__(
        self,
        status_code: int,
        message: str,
        error_id: str,
        details: dict[str, Any] | None = None,
        resource: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.id_ = error_id
        self.details = details or {}
        self.resource = resource


def handle_api_exception(
    func: Callable[..., R]
) -> Callable[..., R | tuple[dict[str, Any], int]]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> R | tuple[dict[str, Any], int]:
        try:
            return func(*args, **kwargs)
        except APIException as error:
            response = {
                'message': error.message,
                'error_id': error.id_,
                'details': error.details,
                'timestamp': time.time(),
            }
            if error.resource:
                response['resource'] = error.resource
            logger.error('%s: %s', error.message, error.details)
            return response, error.status_code

    return wrapper


def load_all_api_specs(
    entry_point_group: str, spec_filename: str
) -> Generator[dict[str, Any], None, None]:
    for module in iter_entry_points(group=entry_point_group):
        try:
            spec = yaml.safe_load(resource_string(module.module_name, spec_filename))
            yield spec
        except OSError:
            logger.debug('API spec for module "%s" does not exist', module.module_name)
        except ImportError as e:
            logger.warning('Could not load module %s: %s', module.module_name, e)
