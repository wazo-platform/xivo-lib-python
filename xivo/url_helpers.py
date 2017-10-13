# -*- coding: utf-8 -*-
# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from requests.utils import quote


def base_join(base, *fragments):
    path = '/'.join(quote(unicode(fragment)).strip('/') for fragment in fragments)
    return "{base}/{path}".format(base=base.strip('/'), path=path)
