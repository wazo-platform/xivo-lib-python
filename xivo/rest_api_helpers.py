# Copyright 2016-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import importlib.resources
import logging
import time
from collections.abc import Callable, Generator
from functools import wraps
from importlib.metadata import entry_points
from typing import Any, TypeVar

import yaml

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
    func: Callable[..., R],
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
) -> Generator[dict[str, Any]]:
    for ep in entry_points(group=entry_point_group):
        package_name = ep.value.split(':')[0].rsplit('.', 1)[0]
        try:
            spec = yaml.safe_load(
                importlib.resources.files(package_name)
                .joinpath(spec_filename)
                .read_bytes()
            )
            yield spec
        except OSError:
            logger.debug('API spec for package "%s" does not exist', package_name)
        except ImportError as e:
            logger.warning('Could not load package %s: %s', package_name, e)
