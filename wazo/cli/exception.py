# Copyright 2013-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later


class CommandAlreadyRegisteredError(Exception):
    pass


class NoMatchingCommandError(Exception):
    pass


class UsageError(Exception):
    pass
