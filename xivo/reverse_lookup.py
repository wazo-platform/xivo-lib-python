# Copyright 2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import phonenumbers


def format_number(number: str) -> str:
    parsed_number = number
    if number[0] == '+':
        parsed_number = phonenumbers.parse(number).national_number
    return parsed_number
