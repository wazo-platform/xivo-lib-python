# -*- coding: utf-8 -*-
# Copyright 2017 The Wazo Authors  (see AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+


def escape(acl_part):
    return acl_part.replace('.', '__DOT__').replace('#', '__HASH__').replace('*', '__STAR__')
