# Copyright 2013-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later


def identity_from_channel(channel):
    last_dash = channel.rfind('-')
    if channel.startswith('Local/'):
        end = channel[-2:]
    else:
        end = ''
    return channel[:last_dash].lower() + end
