# Copyright 2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from collections.abc import Iterator

import pytest
from pytest import FixtureRequest
from wazo_test_helpers.asset_launching_test_case import NoSuchService


@pytest.fixture(autouse=True, scope='function')
def mark_logs(request: FixtureRequest) -> Iterator[None]:
    test_name = f'{request.cls.__name__}.{request.function.__name__}'
    try:
        request.cls.mark_logs_test_start(test_name)
    except NoSuchService:
        pass

    yield

    try:
        request.cls.mark_logs_test_end(test_name)
    except NoSuchService:
        pass
