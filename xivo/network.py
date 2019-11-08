# -*- coding: utf-8 -*-
# Copyright 2007-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import re
import subprocess
import logging
import socket
import struct


log = logging.getLogger("xivo.network")  # pylint: disable-msg=C0103


def is_ipv4_address_valid(addr):
    "True <=> valid"
    try:
        socket.inet_aton(addr)
        return True
    except socket.error:
        return False


def is_mac_address_valid(addr):
    "True <=> valid"
    elements = addr.split(":", 6)
    if len(elements) != 6:
        return False
    for elt in elements:
        try:
            i = int(elt, 16)
        except ValueError:
            return False
        if not (0 <= i < 256):
            return False
    return True


def parse_ipv4(straddr):
    """
    Return an IPv4 address as a 4uple of ints
    @straddr: IPv4 address stored as a string

    >>> parse_ipv4("192.168.0.050")
    (192, 168, 0, 40)
    >>> parse_ipv4("192.168.0.0xA")
    (192, 168, 0, 10)
    >>> parse_ipv4("192.168.0.42")
    (192, 168, 0, 42)
    >>> parse_ipv4("192.168.42")
    (192, 168, 0, 42)
    >>> parse_ipv4("192.168.16383")
    (192, 168, 63, 255)
    >>> parse_ipv4("16383")
    (0, 0, 63, 255)
    >>> parse_ipv4("1")
    (0, 0, 0, 1)
    >>> parse_ipv4("1.13")
    (1, 0, 0, 13)
    """
    return struct.unpack("BBBB", socket.inet_aton(straddr))


_m = None
_valid_netmask = frozenset(
    [
        struct.unpack("BBBB", struct.pack(">L", 0xFFFFFFFF ^ ((1 << _m) - 1)))
        for _m in range(0, 33)
    ]
)
del _m


def plausible_netmask(addr):
    """
    Check that addr (4uple of ints) makes a plausible netmask
    (set bits first, reset bits last)

    >>> plausible_netmask((255, 255, 255, 255))
    True
    >>> plausible_netmask((0, 0, 0, 0))
    True
    >>> plausible_netmask((255, 255, 128, 0))
    True
    >>> plausible_netmask((255, 255, 64, 0))
    False
    """
    return addr in _valid_netmask


# WARNING: the following function does not test the length which must be <= 63
DomainLabelOk = re.compile(r'[a-zA-Z0-9]([-a-zA-Z0-9]*[a-zA-Z0-9])?$').match


def plausible_search_domain(search_domain):
    """
    Return True if the search_domain is suitable for use in the search
    line of /etc/resolv.conf, else False.
    """
    # NOTE: 251 comes from FQDN 255 maxi including label length bytes, we
    # do not want to validate search domain beginning or ending with '.',
    # 255 seems to include the final '\0' length byte, so a FQDN is 253
    # char max.  We remove 2 char so that a one letter label requested and
    # prepended to the search domain results in a FQDN that is not too long
    return (
        search_domain
        and len(search_domain) <= 251
        and all(
            (
                ((len(label) <= 63) and DomainLabelOk(label))
                for label in search_domain.split('.')
            )
        )
    )


def _execute_cmd(cmd):
    log.debug('command: %s', cmd)
    p = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    stdout = p.communicate()[0]

    return (p.returncode, stdout)


if __name__ == "__main__":

    def _test():
        import doctest

        doctest.testmod()

    _test()
