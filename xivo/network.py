# -*- coding: utf-8 -*-
# Copyright 2007-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Network related routines for XIVO

WARNING: Linux specific module, needs /sys/ - also Debian Etch specific module
"""

import re
import os
import subprocess
import logging
import socket
import struct


log = logging.getLogger("xivo.network")  # pylint: disable-msg=C0103


SYS_CLASS_NET = "/sys/class/net"
# /sys/class/net/<ifname>/carrier tells us if the interface if plugged
CARRIER = "carrier"

DECIMAL_SPLIT = re.compile(r'(\d+)').split


def to_int_if_possible(s):
    try:
        return int(s)
    except ValueError:
        return s


def split_alpha_num(s):
    """
    Split the non decimal and the decimal parts of s.
    Don't interpret decimal parts as integers, keep them as string.

    Exemples:

    >>> split_alpha_num('wazza42sub10')
    ('wazza', '42', 'sub', '10')
    >>> split_alpha_num('42sub010')
    ('', '42', 'sub', '010')
    >>> split_alpha_num('a42sub')
    ('a', '42', 'sub')
    >>> split_alpha_num('')
    ('',)
    """
    a_n_splitted = DECIMAL_SPLIT(s)
    if len(a_n_splitted) > 1 and a_n_splitted[-1] == '':
        strs = a_n_splitted[:-1]
    else:
        strs = a_n_splitted
    return tuple(strs)


def split_lexdec(lexdec_str):
    """
    Split the non decimal and the decimal parts of lexdec_str

    Exemples:

    >>> split_lexdec('wazza42sub10')
    ('wazza', 42, 'sub', 10)
    >>> split_lexdec('42sub010')
    ('', 42, 'sub', 10)
    >>> split_lexdec('a42sub')
    ('a', 42, 'sub')
    >>> split_lexdec('')
    ('',)
    """
    return tuple(map(to_int_if_possible, split_alpha_num(lexdec_str)))


def unsplit_lexdec(lexdec_seq):
    """
    Invert of split_lexdec()

    WARNING: unsplit_lexdec(split_lexdec("a0001")) == "a1"
    """
    return ''.join(map(str, lexdec_seq))


def cmp_lexdec(x_str, y_str):
    """
    Compare the splitted versions of x_str and y_str
    """
    x = split_lexdec(x_str)
    y = split_lexdec(y_str)
    return (x > y) - (x < y)


def sorted_lst_lexdec(seqof_lexdec_str):
    """
    Sort ifnames according to their split_lexdec() representations
    Return a list.
    NOTES:
    * The sorting is NOT done in place.
    * This function do not strip leading zeros in decimal parts; elements
      are preserved as they are.
    """
    return sorted(seqof_lexdec_str, cmp=cmp_lexdec)


def is_linux_netdev_if(ifname):
    """
    Return True if ifname seems to be the name of an interface
    """
    return os.path.isdir(os.path.join(SYS_CLASS_NET, ifname))


def get_linux_netdev_list():
    """
    Get an unfiltered view of network interfaces as seen by Linux
    """
    return [entry for entry in os.listdir(SYS_CLASS_NET) if is_linux_netdev_if(entry)]


def get_filtered_ifnames(ifname_match_func=lambda x: True):
    """
    Return the filtered list of network interfaces
    """
    return filter(ifname_match_func, get_linux_netdev_list())


def is_phy_if(ifname):
    """
    Return True iff ifname seems to be the name of a physical interface
    (not a tagged VLAN).
    """
    return '.' not in ifname


def get_filtered_phys(ifname_match_func=lambda x: True):
    """
    Return the filtered list of network interfaces which are not VLANs
    (the interface name does not contain a '.')
    """
    return [dev for dev in get_filtered_ifnames(ifname_match_func) if is_phy_if(dev)]


def is_interface_plugged(ifname):
    """
    WARNING: Only works on physical interfaces
    """
    try:
        with open(os.path.join(SYS_CLASS_NET, ifname, CARRIER), 'r') as f:
            return bool(int(f.read().strip()))
    except IOError:
        return False


def normalize_ipv4_address(addr):
    """
    Return a canonical string repr of addr (which must be a valid IPv4)

    >>> normalize_ipv4_address("1.2.3.077")
    '1.2.3.63'
    >>> normalize_ipv4_address("1.2.3.4")
    '1.2.3.4'
    >>> normalize_ipv4_address("1.2.259")
    '1.2.1.3'
    >>> normalize_ipv4_address("4")
    '0.0.0.4'
    >>> normalize_ipv4_address("1.13")
    '1.0.0.13'
    >>> normalize_ipv4_address("1.16383")
    '1.0.63.255'
    >>> normalize_ipv4_address("0xA.0xa.0x00a.012")
    '10.10.10.10'
    """
    return socket.inet_ntoa(socket.inet_aton(addr))


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


def format_ipv4(tupaddr):
    """
    Return a string repr of an IPv4 internal repr
    @tupaddr is an IPv4 address stored as a tuple of 4 ints

    >>> format_ipv4((192, 168, 0, 42))
    '192.168.0.42'
    >>> format_ipv4((192, 168, 63, 255))
    '192.168.63.255'
    >>> format_ipv4((0, 0, 63, 255))
    '0.0.63.255'
    >>> format_ipv4((0, 0, 0, 1))
    '0.0.0.1'
    >>> format_ipv4((1, 0, 0, 13))
    '1.0.0.13'
    """
    return '.'.join(map(str, tupaddr))


def mask_ipv4(mask, addr):
    """
    Binary AND of IPv4 mask and IPv4 addr
    (mask and addr are 4uple of ints)
    """
    return tuple([m & a for m, a in zip(mask, addr)])


def or_ipv4(mask, addr):
    """
    Binary OR of IPv4 mask and IPv4 addr
    (mask and addr are 4uple of ints)
    """
    return tuple([m | a for m, a in zip(mask, addr)])


def netmask_invert(mask):
    """
    Invert bits in mask
    (mask is 4uple of ints)
    """
    return tuple([m ^ 0xFF for m in mask])


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
