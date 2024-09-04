# Copyright 2013-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations


def identity_from_channel(channel: str) -> str:
    last_dash = channel.rfind('-')
    if channel.startswith('Local/'):
        end = channel[-2:]
    else:
        end = ''
    return channel[:last_dash].lower() + end
