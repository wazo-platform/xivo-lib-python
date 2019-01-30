# -*- coding: utf-8 -*-
# Copyright (C) 2007-2014 Avencall
# SPDX-License-Identifier: GPL-3.0-or-later

from collections import namedtuple


Extension = namedtuple('FullExtension', ['number', 'context', 'is_internal'])
Extension.__repr__ = lambda self: '%s@%s' % (self.number, self.context)
