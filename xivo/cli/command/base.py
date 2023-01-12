# Copyright 2013-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import Any, NoReturn


class BaseCommand:
    help: str
    usage: str | None

    def prepare(self, command_args: list[str]) -> tuple[Any, ...]:
        return ()

    def execute(self, *args: Any, **kwargs: Any) -> NoReturn | None:
        # must be overriden in derived class
        raise NotImplementedError()
