# Copyright 2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import logging

import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat, is_valid_number

logger = logging.getLogger(__name__)


def format_number(number: str, country_code: str | None = None) -> str | None:
    parsed_number = None
    try:
        parsed_number = phonenumbers.parse(number, country_code)
    except NumberParseException:
        logger.debug(
            f'Could not parse number {number} with country code {country_code}'
        )

    if parsed_number is None or not is_valid_number(parsed_number):
        return None
    return phonenumbers.format_number(parsed_number, PhoneNumberFormat.E164)
