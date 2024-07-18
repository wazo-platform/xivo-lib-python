# Copyright 2013-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import NoReturn

from xivo.cli.command.base import BaseCommand


class ExitCommand(BaseCommand):
    help = 'Exit the interpreter'
    usage = None

    def execute(self) -> NoReturn:
        raise SystemExit()
