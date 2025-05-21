# Copyright 2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import logging

import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat, is_valid_number

logger = logging.getLogger(__name__)


def format_phone_number_e164(
    number: str, country_code: str | None = None
) -> str | None:
    """
    Format the given number to E164 standard, based on the country code.
    If the number is already in the E164 format, its original country
    code is kept. In the case the number can't be formatted, 'None' is
    returned.

    Args:
        number (str): The phone number to try to format
        country_code (str): The country code to use

    Returns:
        str | None: The formatted phone number or None if the number
                   could not be formatted
    """
    return _format_phone_number(number, PhoneNumberFormat.E164, country_code)


def _format_phone_number(
    number: str, number_format: PhoneNumberFormat, country_code: str | None = None
) -> str | None:
    parsed_number = None
    try:
        parsed_number = phonenumbers.parse(number, country_code)
    except NumberParseException:
        logger.debug(
            f'Could not parse number {number} with country code {country_code}'
        )

    if parsed_number is None or not is_valid_number(parsed_number):
        return None
    return phonenumbers.format_number(parsed_number, number_format)
