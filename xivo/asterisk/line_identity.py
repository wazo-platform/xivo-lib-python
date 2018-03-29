# -*- coding: utf-8 -*-
# Copyright (C) 2013-2014 Avencall
# SPDX-License-Identifier: GPL-3.0+


def identity_from_channel(channel):
    last_dash = channel.rfind('-')
    if channel.startswith('Local/'):
        end = channel[-2:]
    else:
        end = ''
    return channel[:last_dash].lower() + end
