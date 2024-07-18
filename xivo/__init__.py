# Copyright 2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import warnings

import wazo

warnings.simplefilter('module', category=DeprecationWarning)
warnings.warn(
    f'{__name__} is deprecated and will be removed in the future, '
    'Please use `wazo` instead.',
    DeprecationWarning,
    stacklevel=2,
)

# Note: Alias xivo to wazo
sys.modules['xivo'] = wazo
