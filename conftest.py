# Copyright 2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import sys

collect_ignore = []
if sys.version_info.major < 3:
    collect_ignore = [
        'xivo/mallow/tests/test_fields.py',
        'xivo/mallow/tests/test_validate.py',
        'xivo/tests/test_mallow_helpers.py',
    ]
