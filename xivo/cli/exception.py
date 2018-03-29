# -*- coding: utf-8 -*-
# Copyright (C) 2013-2014 Avencall
# SPDX-License-Identifier: GPL-3.0+


class CommandAlreadyRegisteredError(Exception):
    pass


class NoMatchingCommandError(Exception):
    pass


class UsageError(Exception):
    pass
