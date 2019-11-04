# -*- coding: utf-8 -*-
# Copyright 2007-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Common routines services in XIVO

"""
# Dependencies/highly recommended? : arping curl

import os
import copy
import yaml
import logging

from itertools import chain, count
from xivo import network
from xivo import system
from xivo import xys


log = logging.getLogger("xivo.xivo_config")  # pylint: disable-msg=C0103


SYSCONF_DIR = "/etc/xivo/sysconf"

STORE_BASE = os.path.join(SYSCONF_DIR, "store")

STORE_DEFAULT = "default"
STORE_CURRENT = "current"
STORE_PREVIOUS = "previous"
STORE_TMP = "tmp"
STORE_NEW = "new"
STORE_FAILED = "failed"
STORE_RESERVED = (
    STORE_DEFAULT,
    STORE_CURRENT,
    STORE_PREVIOUS,
    STORE_TMP,
    STORE_NEW,
    STORE_FAILED,
)

GENERATED_BASE = os.path.join(SYSCONF_DIR, "generated")

GENERATED_CURRENT = "current"
GENERATED_PREVIOUS = "previous"
GENERATED_TMP = "tmp"
GENERATED_NEW = "new"

NETWORK_CONFIG_FILE = "network.yaml"

#                                   path used by system:
INTERFACES_FILE = "interfaces"  # /etc/network/
DHCPD_CONF_FILE = "dhcpd.conf"  # /etc/dhcp/
IFPLUGD_FILE = "ifplugd"  # /etc/default/

AUTHORIZED_PREFIXES = ("en", "eth", "vlan", "dummy")


def netif_managed(ifname):
    """
    Return True iff ifname seems to be a name of a network interface that must
    be managed by this module.
    """
    return True in [ifname.startswith(x) for x in AUTHORIZED_PREFIXES]


# States for linesubst()
NORM = object()
ONE = object()
TWO = object()
LIT = object()
TLIT = object()
TERM = object()


def linesubst(line, variables):
    """
    In a string, substitute '{{varname}}' occurrences with the value of
    variables['varname'], '\\' being an escaping char...
    If at first you don't understand this function, draw its finite state
    machine and everything will become crystal clear :)
    """
    # trivial no substitution early detection:
    if '{{' not in line and '\\' not in line:
        return line
    st = NORM
    out = ""
    curvar = ""
    for c in line:
        if st is NORM:
            if c == '{':
                st = ONE
            elif c == '\\':
                st = LIT
            else:
                out += c
        elif st is LIT:
            out += c
            st = NORM
        elif st is ONE:
            if c == '{':
                st = TWO
            elif c == '\\':
                out += '{'
                st = LIT
            else:
                out += '{' + c
                st = NORM
        elif st is TWO:
            if c == '\\':
                st = TLIT
            elif c == '}':
                st = TERM
            else:
                curvar += c
        elif st is TLIT:
            curvar += c
            st = TWO
        elif st is TERM:
            if c == '}':
                if curvar not in variables:
                    log.warning(
                        "Unknown variable %r detected, will just be replaced by an empty string",
                        curvar,
                    )
                else:
                    log.debug("Substitution of {{%s}} by %r", curvar, variables[curvar])
                    out += variables[curvar]
                curvar = ''
                st = NORM
            elif c == '\\':
                curvar += '}'
                st = TLIT
            else:
                curvar += '}' + c
                st = TWO
    if st is not NORM:
        log.warning("st is not NORM at end of line: " + line)
        log.warning("returned substitution: " + out)
    return out


def txtsubst(lines, variables, target_file=None, charset=None):
    """
    Log that target_file is going to be generated, and calculate its
    content by applying the linesubst() transformation with the given
    variables to each given lines.
    """
    if target_file:
        log.info("In process of generating file %r", target_file)

    if not charset:
        return [linesubst(line, variables) for line in lines]

    ret = []
    for line in lines:
        linesub = linesubst(line, variables)
        if isinstance(line, unicode):
            ret.append(linesub.encode(charset))
        else:
            ret.append(linesub)
    return ret


ID_CHR = ''.join(map(chr, xrange(0, 256)))

PhoneClasses = {}

# ## GENERAL CONF


def specific(nstr):
    return nstr not in ('reserved', 'none', 'void', 'removed')


def specific_or_reserved(nstr):
    return nstr not in ('none', 'void', 'removed')


def network_from_static(static):
    """
    Return the network (4uple of ints) specified in static
    """
    return network.mask_ipv4(
        network.parse_ipv4(static['netmask']), network.parse_ipv4(static['address'])
    )


def broadcast_from_static(static):
    """
    Return the broadcast address (4uple of ints) specified in static
    """
    if 'broadcast' in static:
        return network.parse_ipv4(static['broadcast'])
    else:
        return network.or_ipv4(
            network.netmask_invert(network.parse_ipv4(static['netmask'])),
            network_from_static(static),
        )


def netmask_from_static(static):
    return network.parse_ipv4(static['netmask'])


def ip_in_network(ipv4, net, netmask):
    """
    Return a tuple (innet, other_net) where innet is a boolean that is True
    iff ipv4/netmask is the same as net and other_net is ipv4/netmask.
    """
    other_net = network.mask_ipv4(netmask, ipv4)
    return (net == other_net), other_net


def domain_label(nstr, schema):
    """
    !~domain_label
        Return True if the document string is a domain label, else False
    """
    return network.DomainLabelOk(nstr) and len(nstr) <= 63


def search_domain(nstr, schema):
    """
    !~search_domain
        Return True if the document string is suitable for use in the
        search line of /etc/resolv.conf, else False
    """
    return network.plausible_search_domain(nstr)


def macaddr(nstr, schema):
    """
    !~macaddr
        Check that the document string is an ethernet mac addresses
    """
    return network.is_mac_address_valid(nstr)


def ipv4_address(nstr, schema):
    """
    !~ipv4_address
        Check that the document string is an IPv4 addresses
    """
    return network.is_ipv4_address_valid(nstr)


def ipv4_address_or_domain(nstr, schema):
    """
    !~ipv4_address_or_domain
        Return True if the document string is an IPv4 address
        or a domain, else False
    """
    return network.is_ipv4_address_valid(nstr) or network.plausible_search_domain(nstr)


def netmask(nstr, schema):
    """
    !~netmask
        Check that the document string is an IPv4 netmasks
    """
    return network.is_ipv4_address_valid(nstr) and network.plausible_netmask(
        network.parse_ipv4(nstr)
    )


def specific_prefixDec(fname, prefix):
    """
    Return a XYS validator that checks that corresponding document strings
    are 'reserved', 'none', 'void', 'removed' or valid per !~~prefixDec prefix.
    """

    def validator(nstr, schema):
        """
        !~<validator generated by specific_prefixDec() >
            Checks that corresponding document strings are 'reserved',
            'none', 'void', 'removed' or valid per !~~prefixDec prefix.
        """
        if nstr in ('reserved', 'none', 'void', 'removed'):
            return True
        if not nstr.startswith(prefix):
            return False
        try:
            int(nstr[len(prefix) :])
        except ValueError:
            return False
        return True

    validator.__name__ = fname  # pylint: disable-msg=W0621
    return validator


def get_referenced_ipConfTags(conf):
    """
    Get tags of the static IP configurations that are owned by vlans (in
    our relational model vlans include untaggued vlan and physical
    interfaces are never directly related to IP configurations).

    Return a list
    """
    return filter(
        specific, chain(*[elt.itervalues() for elt in conf['vlans'].itervalues()])
    )


def get_referenced_vsTags(conf):
    """
    Get tags of the VLan sets that are owned by a physical interface.

    Return a list
    """
    return filter(specific, conf['netIfaces'].itervalues())


def references_relation(set_defined_symbols, lst_references, minref, maxref):
    """
    Pure function.

    For each element of set_defined_symbols, there must be between minref
    and maxref, included, identical elements in references.

    This function returns (dict_ok, dict_out_of_bounds, dict_undefined)
    where dictionaries contain entries of symbol: count.

    Any symbol of set_defined_symbols appears either in dict_ok or in
    dict_out_of_bounds, even if it is unreferenced: in this case count == 0
    """
    dict_ok = {}
    dict_out_of_bounds = {}
    dict_undefined = {}

    dict_count = {}

    for symbol in lst_references:
        if symbol in set_defined_symbols:
            dict_count[symbol] = dict_count.get(symbol, 0) + 1
        else:
            dict_undefined[symbol] = dict_undefined.get(symbol, 0) + 1

    for symbol in set_defined_symbols:
        cnt = dict_count.get(symbol, 0)
        if minref <= cnt <= maxref:
            dict_ok[symbol] = cnt
        else:
            dict_out_of_bounds[symbol] = cnt

    return dict_ok, dict_out_of_bounds, dict_undefined


def plausible_configuration(conf, schema):
    """
    !~plausible_configuration
        Validate the general system configuration
    """

    dict_ok, dict_out_of_bounds, dict_undefined = references_relation(
        conf['ipConfs'], get_referenced_ipConfTags(conf), minref=0, maxref=1
    )
    if dict_out_of_bounds:
        log.error(
            "duplicated static IP conf references in vlans description: %r",
            dict_out_of_bounds,
        )
        return False
    if dict_undefined:
        log.error("undefined referenced static IP configurations: %r", dict_undefined)
        return False

    referenced_vsTags = get_referenced_vsTags(conf)
    dict_ok, dict_out_of_bounds, dict_undefined = references_relation(
        conf['vlans'], referenced_vsTags, minref=0, maxref=1
    )
    if dict_out_of_bounds:
        log.error(
            "duplicated vlan references in network interfaces description: %r",
            dict_out_of_bounds,
        )
        return False
    if dict_undefined:
        log.error("undefined vlan configurations: %r", dict_undefined)
        return False

    # TODO: uniqueness concept in schema, default types in schema
    nameservers = conf['resolvConf'].get('nameservers')
    if nameservers:
        nameservers = map(network.normalize_ipv4_address, nameservers)
        unique_nameservers = frozenset(nameservers)
        if len(unique_nameservers) != len(nameservers):
            log.error("duplicated nameservers in %r", tuple(nameservers))
            return False

    # Check that active networks are distinct
    active_networks = {}
    duplicated_networks = False
    for vlanset_name in referenced_vsTags:
        for static_name in conf['vlans'][vlanset_name].itervalues():
            if not specific(static_name):
                continue
            net = network_from_static(conf['ipConfs'][static_name])
            if net in active_networks:
                duplicated_networks = True
                active_networks[net].append(static_name)
            else:
                active_networks[net] = [static_name]
    if duplicated_networks:
        non_duplicated_networks = [
            net for net, names in active_networks.iteritems() if len(names) <= 1
        ]
        for net in non_duplicated_networks:
            del active_networks[net]
        log.error(
            "duplicated active networks: %r",
            dict(
                (
                    ('.'.join(map(str, net)), tuple(names))
                    for net, names in active_networks.iteritems()
                )
            ),
        )
        return False

    # VOIP service
    ipConfVoip = conf['services']['voip']['ipConf']
    if ipConfVoip not in conf['ipConfs']:
        log.error(
            "the voip service references a static ip configuration that does not exists: %r",
            ipConfVoip,
        )
        return False
    ipConfVoip_static = conf['ipConfs'][ipConfVoip]
    netmask = netmask_from_static(ipConfVoip_static)
    net = network_from_static(ipConfVoip_static)
    broadcast = broadcast_from_static(ipConfVoip_static)
    addresses = conf['services']['voip']['addresses']
    voip_fixed = ('voipServer', 'bootServer', 'directory', 'ntp', 'router')
    for field in voip_fixed:
        if field in addresses:
            if (
                network.parse_ipv4(addresses[field]) == broadcast
            ):  # TODO: other sanity checks...
                log.error(
                    "invalid voip service related IP %r: %r", field, addresses[field]
                )
                return False
    # router, if present, must be in the network
    if 'router' in addresses:
        ok, other = ip_in_network(network.parse_ipv4(addresses['router']), net, netmask)
        if not ok:
            log.error(
                "router must be in network %s/%s but seems to be in %s/%s",
                network.format_ipv4(net),
                network.format_ipv4(netmask),
                network.format_ipv4(other),
                network.format_ipv4(netmask),
            )
            return False
    # check that any range is in the network and with min <= max
    for range_field in 'voipRange', 'alienRange':
        if range_field not in addresses:
            continue
        ip_range = map(network.parse_ipv4, addresses[range_field])
        for ip in ip_range:
            ok, other = ip_in_network(ip, net, netmask)
            if not ok:
                log.error(
                    "IP %s is not in network %s/%s",
                    network.format_ipv4(ip),
                    network.format_ipv4(net),
                    network.format_ipv4(netmask),
                )
                return False
        if not (ip_range[0] <= ip_range[1]):
            log.error("Invalid IP range: %r", tuple(addresses[range_field]))
            return False
    # check that there is no overlapping ranges
    parsed_voipRange = map(network.parse_ipv4, addresses['voipRange'])
    all_ranges = [parsed_voipRange]
    if 'alienRange' in addresses:
        one = parsed_voipRange
        two = map(network.parse_ipv4, addresses['alienRange'])
        all_ranges.append(two)
        if (one[0] <= two[0] <= one[1]) or (one[0] <= two[1] <= one[1]):
            log.error("overlapping DHCP ranges detected")
            return False
    # check that there is no fixed IP in any DHCP range
    fixed_addresses = [
        network.parse_ipv4(ipConfVoip_static[field])
        for field in ('address', 'gateway')
        if field in ipConfVoip_static
    ]
    fixed_addresses.append(broadcast_from_static(ipConfVoip_static))
    fixed_addresses.extend(
        [
            network.parse_ipv4(addresses[field])
            for field in voip_fixed
            if field in addresses
        ]
    )
    for rang in all_ranges:
        for addr in fixed_addresses:
            if rang[0] <= addr <= rang[1]:
                log.error(
                    "fixed address %r detected in DHCP range %r",
                    network.format_ipv4(addr),
                    tuple(rang),
                )
                return False

    return True


xys.add_validator(domain_label, u'!!str')
xys.add_validator(search_domain, u'!!str')
xys.add_validator(ipv4_address, u'!!str')
xys.add_validator(ipv4_address_or_domain, u'!!str')
xys.add_validator(netmask, u'!!str')
xys.add_validator(macaddr, u'!!str')
xys.add_validator(plausible_static, u'!!map')
xys.add_validator(plausible_configuration, u'!!map')
xys.add_validator(specific_prefixDec('vlanIpConf', 'static_'), u'!!str')
xys.add_validator(specific_prefixDec('netIfaceVlans', 'vs_'), u'!!str')


SCHEMA_NETWORK_CONFIG = xys.load(
    """!~plausible_configuration
resolvConf:
    search?: !~search_domain bla.tld
    nameservers?: !~~seqlen(1,3) [ !~ipv4_address 192.168.0.200 ]
ipConfs:
    !~~prefixedDec static_: !~plausible_static
        address:    !~ipv4_address 192.168.0.100
        netmask:    !~netmask 255.255.255.0
        broadcast?: !~ipv4_address 192.168.0.255
        gateway?:   !~ipv4_address 192.168.0.254
        mtu?:       !~~between(68,1500) 1500
vlans:
    !~~prefixedDec vs_:
        !~~between(0,4094) 0: !~vlanIpConf static_0001
netIfaces:
    !~~prefixedDec eth: !~netIfaceVlans vs_0001
services:
    voip:
        ipConf: !~~prefixedDec static_
        addresses:
            voipServer:  !~ipv4_address 192.168.1.200
            bootServer:  !~ipv4_address 192.168.1.200
            voipRange:   !~~seqlen(2,2) [ !~ipv4_address 192.168.1.200 ]
            alienRange?: !~~seqlen(2,2) [ !~ipv4_address 192.168.1.200 ]
            directory?:  !~ipv4_address 192.168.1.200
            ntp?:        !~ipv4_address 192.168.1.200
            router?:     !~ipv4_address 192.168.1.254
"""
)

# TODO:
# ipConfs:
# 	static_xxxx:
# 		comment:
# dont le contenu sera injecte dans /e/n/i

# TODO creer un program qui fill les truc par defaut non remplis de network.yaml

# TODO interface de lookup inverse: envoyer la liste des static_xxxx => mac addr + VLan ID


def normalize_static(static):
    """
    Normalize IPv4 addresses in static
    """
    # TODO: check before normalization, or better schema for not only formatting but also typing
    for key in ('address', 'netmask', 'broadcast', 'gateway'):
        if key in static:
            static[key] = network.normalize_ipv4_address(static[key])


class InvalidConfigurationError(Exception):
    "Error raised when a configuration is detected as semantically invalid."

    def __init__(self, msg):
        self.__reprmsg = "<%s %r>" % (self.__class__.__name__, msg)
        self.__strmsg = str(msg)
        Exception.__init__(self, msg)

    def __repr__(self):
        return self.__reprmsg

    def __str__(self):
        return self.__strmsg


def load_configuration(conf_source):
    """
    Parse the first YAML document in a stream and produce the corresponding
    normalized internal representation of the configuration.

    Raise a xivo_config.InvalidConfigurationError if the configuration is
    invalid.
    """
    conf = yaml.safe_load(conf_source)
    if not xys.validate(conf, SCHEMA_NETWORK_CONFIG):
        raise InvalidConfigurationError("Invalid configuration")
    # TODO: do that thanks to a schema based mapping ("mapping" in functional programming meaning)
    nameservers = conf['resolvConf'].get('nameservers')
    if nameservers:
        conf['resolvConf']['nameservers'] = map(
            network.normalize_ipv4_address, nameservers
        )
    for static in conf['ipConfs'].itervalues():
        normalize_static(static)
    voip_addresses = conf['services']['voip']['addresses']
    for field in 'voipServer', 'bootServer', 'directory', 'ntp', 'router':
        if field in voip_addresses:
            voip_addresses[field] = network.normalize_ipv4_address(
                voip_addresses[field]
            )
    for range_name in 'voipRange', 'alienRange':
        if range_name in voip_addresses:
            voip_addresses[range_name][:] = map(
                network.normalize_ipv4_address, voip_addresses[range_name]
            )
    return conf


def save_configuration(conf, file_obj):
    """
    Serialize the internal representation of the configuration to @file_obj
    in YAML.

    This can only be done if the configuration is valid.
    InvalidConfigurationError will be raised if the configuration is not
    valid.
    """
    if not xys.validate(conf, SCHEMA_NETWORK_CONFIG):
        raise InvalidConfigurationError("Invalid configuration")
    result = yaml.safe_dump(conf, stream=file_obj, default_flow_style=False, indent=4)
    system.flush_sync_file_object(file_obj)
    return result


def load_current_configuration():
    """
    Load the configuration from the standard current path.
    """
    return load_configuration(
        file(os.path.join(STORE_BASE, STORE_CURRENT, NETWORK_CONFIG_FILE))
    )


def save_configuration_for_transaction(conf):
    """
    Serialize the internal representation of the XIVO configuration in a
    file that will be used during the system configuration generation
    transaction.
    """
    return save_configuration(
        conf,
        system.file_w_create_directories(
            os.path.join(STORE_BASE, STORE_TMP, NETWORK_CONFIG_FILE)
        ),
    )


class TransactionError(Exception):
    "Error raised on transaction cancellation."

    def __init__(self, msg, original_exception=None):
        self.__reprmsg = "<%s %r>" % (self.__class__.__name__, msg)
        self.__strmsg = str(msg)
        self.original_exception = original_exception
        Exception.__init__(self, msg)

    def __repr__(self):
        return self.__reprmsg

    def __str__(self):
        return self.__strmsg


def rotate_entries(previous, current, new):
    """
    If current exists:
      1) Delete previous.
      2) Move current to previous.
    3) Finally, move new to current.

    OSError exceptions raised during 1) are ignored (but traced).
    OSError exceptions during 2) are handled by trying to delete current
    instead.
    Other exceptions are not catched.
    """
    log.info(
        "Entering rotate_entries(previous=%r, current=%r, new=%r)",
        previous,
        current,
        new,
    )

    if os.path.exists(current):
        log.info("%r to %r", current, previous)

        log.debug("about to remove %r", previous)
        try:
            system.rm_rf(previous)
        except OSError:
            log.warning("rotate_entries: failed to delete %r", previous, exc_info=True)

        log.debug("about to rename %r to %r", current, previous)
        try:
            os.rename(current, previous)
        except OSError:
            log.warning(
                "rotate_entries: failed to rename %r to %r",
                current,
                previous,
                exc_info=True,
            )
            system.rm_rf(current)

        system.sync_no_oserror()

    log.debug("about to rename %r to %r", new, current)
    os.rename(new, current)

    system.sync_no_oserror()

    log.info("Leaving rotate_entries.")


def transactional_generation(
    store_base, store_subs, gen_base, gen_subs, generation_func
):
    """
    This function first removes some temporary directories.  Then it
    completes a three staged transaction if it has been started, or does
    nothing otherwise.  The purpose of the transaction is to generate some
    configuration files from others.  The source files are all stored along
    in a common subdirectory, and the destination files are in an other
    subdirectory.  The transaction guaranty as much as possible (we depends
    on the filesystem) that in the stable state the source and the
    destination configurations are in sync.  The transaction must be
    externally initiated by the creation of the new store entry in the
    filesystem.

    This function returns True if a transaction has been processed
    successfully or None if no transaction was in progress.  A transaction
    fails and is cancelled iff generation_func() raises an exception; in
    this case a TransactionError is raised.  Uncatched exceptions raised by
    transactional_generation() must be considered as fatal errors requiring
    human intervention or at least restoration of a known stable state.

    If this function returns with no exception, the resulting state is
    stable and clean; there are no remaining temporary directories.

    @store_base: base directory of source configurations.
    @store_subs: sub-paths from store_base to previous, current, new, tmp,
                 and failed.
    @gen_base: base directory of all generated configurations.
    @gen_subs: sub-paths from gen_base to previous, current, new, and tmp.
    @generation_func(to_gen, prev_gen, current_src):
        where:
        @to_gen: path where the configuration must be generated.
        @prev_gen: path where the previously generated configuration
            stands.  If no configuration has been previously generated,
            prev_gen contains None instead.
        @current_src: path where the source configuration stands.

    NOTE: Because of our requirements some state that is only stored in the
    generated files must be preserved (configuration of reserved interfaces
    and of unhandled interfaces).  That is why generation_func takes its
    second parameter.
    """
    log.info("ENTERING transactional_generation()")
    log.debug("  store_base = %r", store_base)
    log.debug("  store_subs = %r", store_subs)
    log.debug("  gen_base = %r", gen_base)
    log.debug("  gen_subs = %r", gen_subs)

    store_previous, store_current, store_new, store_tmp, store_failed = [
        os.path.join(store_base, x) for x in store_subs
    ]
    gen_previous, gen_current, gen_new, gen_tmp = [
        os.path.join(gen_base, x) for x in gen_subs
    ]

    for entry in (store_tmp, gen_tmp):
        if os.path.exists(entry):
            log.warning("transactional_generation: removing stalled entry %r", entry)
            system.rm_rf(entry)

    if os.path.exists(store_new) and not os.path.exists(gen_new):
        log.info("BEGIN PHASE 1")

        log.debug("about to remove %r", gen_tmp)
        system.rm_rf(gen_tmp)

        if os.path.exists(gen_current):
            log.info("%r exists", gen_current)
            previously_generated = gen_current
        else:
            log.info("%r does not exist", gen_current)
            previously_generated = None

        log.debug("about to call %r", generation_func)
        log.debug("  gen_tmp = %r", gen_tmp)
        log.debug("  previously_generated = %r", previously_generated)
        log.debug("  store_new = %r", store_new)

        try:
            generation_func(gen_tmp, previously_generated, store_new)

        except Exception as ex:
            log.exception("Error during generation - cancelling transaction")

            system.rm_rf(store_failed)

            log.debug("about to %r rename to %r", store_new, store_failed)
            try:
                os.rename(store_new, store_failed)
            except OSError:
                log.warning(
                    "transactional_generation: failed to rename %r to %r - destroying %r",
                    store_new,
                    store_failed,
                    store_new,
                    exc_info=True,
                )
                system.rm_rf(store_new)

            log.info("about to remove incompletely generated directory %r", gen_tmp)
            system.rm_rf(gen_tmp)

            system.sync_no_oserror()

            log.info("END PHASE 1 - transaction cancelled - raising TransactionError")

            raise TransactionError("generation failure", ex)

        else:
            log.info("Successful generation")

            system.sync_no_oserror()

            log.debug("about to rename %r to %r", gen_tmp, gen_new)
            os.rename(gen_tmp, gen_new)

            system.sync_no_oserror()

            log.info("END PHASE 1 - generation performed")

    if os.path.exists(store_new) and os.path.exists(gen_new):
        log.info("BEGIN PHASE 2")

        rotate_entries(store_previous, store_current, store_new)

        log.info("END PHASE 2")

    if (not os.path.exists(store_new)) and os.path.exists(gen_new):
        log.info("BEGIN PHASE 3")

        rotate_entries(gen_previous, gen_current, gen_new)

        log.info("END PHASE 3")

        log.info("LEAVING transactional_generation - success")
        return True

    log.info("LEAVING transactional_generation - no transaction to complete")


def transaction_system_configuration():
    """
    Transactionally generate system configuration from our own
    configuration model.
    """
    transactional_generation(
        STORE_BASE,
        (STORE_PREVIOUS, STORE_CURRENT, STORE_NEW, STORE_TMP, STORE_FAILED),
        GENERATED_BASE,
        (GENERATED_PREVIOUS, GENERATED_CURRENT, GENERATED_NEW, GENERATED_TMP),
        generate_system_configuration,
    )


def gen_plugged_by_phy(phys):
    """
    Construct a cache of carrier status of interfaces in the sequence phys.
    The cache is a mapping where keys are interfaces and values a boolean
    representing the carrier status:
        (False => disconnected, True => connected)
    """
    return dict(((phy, network.is_interface_plugged(phy)) for phy in phys))


def cmp_bool_lexdec(x, y):
    """
    Let X = (x[0], x[1]) and Y = (y[0], y[1]) where
      x[0] and y[0] are boolean and
      x[1] and y[1] are lexico-decimal strings
        Lexico-decimal strings are totally ordered by the
        network.cmp_lexdec function.

    This function defines a total order on the set of
    boolean times lexico-decimal strings, which X and Y belong to.
    """
    return cmp((x[0], network.split_lexdec(x[1])), (y[0], network.split_lexdec(y[1])))


def aa_lst_npst_phy(conf, plugged_by_phy):
    """
    Return a list of (npst, phy) in cmp_bool_lexdec order.
    @npst: not plugged status
    @phy: physical interfaces name

    Only phys that are in the "void" will be enumerated.
    """
    # TODO: detect the default path of get() and: trace it?
    def phy_handled_relate_void(phy):
        """
        Is phy both handled (its name prefix is known) and in the "void"
        """
        return netif_managed(phy) and conf['netIfaces'].get(phy, 'void') == 'void'

    phys = network.get_filtered_phys(phy_handled_relate_void)
    return sorted(
        ((not plugged_by_phy.get(phy, False), phy) for phy in phys), cmp=cmp_bool_lexdec
    )


def aa_lst_npst_fifn_vsTag_vlanId(conf, plugged_by_phy):
    """
    Return a list of (npst, fifn, vsTag, vlanId) in cmp_bool_lexdec order
    for (npst, fifn) where:
    @npst: True if the supporting interface is not connected (boolean)
    @fifn: "full" interface name - that is the linux vlan interface name
        or ethXX.0 for untagged vlans (string)
    @vsTag: vlan set tag (string)
    @vlanId: vlan Id (integer)

    Only interfaces that are in the "void" will be enumerated.
    """
    res = []
    for phy, vsTag in conf['netIfaces'].iteritems():
        if specific(vsTag):
            for vlanId, ipConfs_tag in conf['vlans'][vsTag].iteritems():
                if ipConfs_tag == 'void':
                    fifn = "%s.%d" % (phy, vlanId)
                    res.append(
                        (not plugged_by_phy.get(phy, False), fifn, vsTag, vlanId)
                    )
    res.sort(cmp=cmp_bool_lexdec)
    return res


def aa_lst_vsTag(conf):
    """
    Return a list of vlan set names that are not owned by a physical
    interface and for which related IP configurations will not be in
    conflict with IP configurations already used or previously selected IP
    configurations.  The list is sorted by network.sorted_lst_lexdec().
    """
    referenced_networks = frozenset(
        [
            network_from_static(conf['ipConfs'][ipConfTag])
            for ipConfTag in get_referenced_ipConfTags(conf)
        ]
    )
    owned = frozenset(get_referenced_vsTags(conf))
    eligible_networks = set()
    unsorted_eligible_vsTag = []
    for vsTag in conf['vlans'].iterkeys():
        if vsTag in owned:
            continue
        new_nets = [
            network_from_static(conf['ipConfs'][ipConfTag])
            for ipConfTag in conf['vlans'][vsTag].itervalues()
            if specific(ipConfTag)
        ]
        set_new_nets = set(new_nets)
        # conflict within the very references of this vset?
        if len(new_nets) != len(set_new_nets):
            continue
        # conflict with networks already referenced or
        if referenced_networks.intersection(
            set_new_nets
        ) or eligible_networks.intersection(set_new_nets):
            continue
        eligible_networks.update(set_new_nets)
        unsorted_eligible_vsTag.append(vsTag)
    return network.sorted_lst_lexdec(unsorted_eligible_vsTag)


def aa_lst_ipConfTag(conf):
    """
    Return a list of ipconf tags that are not owned by a vlan (in our
    terminology vlans include untaggued vlan) for which corresponding IP
    configurations will not be in conflict with IP configurations already
    used or previously selected IP configurations.
    The list is sorted by network.sorted_lst_lexdec().
    """
    owned = frozenset(get_referenced_ipConfTags(conf))
    referenced_networks = frozenset(
        [network_from_static(conf['ipConfs'][ipConfTag]) for ipConfTag in owned]
    )
    eligible_networks = set()
    unsorted_eligible_ipConfTag = []
    for ipConfTag in conf['ipConfs'].iterkeys():
        if ipConfTag in owned:
            continue
        new_net = network_from_static(conf['ipConfs'][ipConfTag])
        if new_net in referenced_networks or new_net in eligible_networks:
            continue
        eligible_networks.add(new_net)
        unsorted_eligible_ipConfTag.append(ipConfTag)
    return network.sorted_lst_lexdec(unsorted_eligible_ipConfTag)


def iter_new_vsTag(conf):
    """
    Yield vsTags that are not yet used.
    """
    return (
        "vs_%04d" % cnt
        for cnt in count(
            max(network.split_lexdec(vsTag)[1] for vsTag in conf['vlans']) + 1
        )
    )


def autoattrib_conf(conf):
    """
    Auto attribute orphan vlan set to 'void' physical interfaces, in
    priority to plugged interfaces then to unplugged interfaces.
    Once done auto attribute vlan interfaces (including untagged vlans) to
    orphan ip configurations.  Finally auto attribute remaining IP
    configuration directly to remaining interfaces, creating trivial vlan
    sets so that the end to end relationship is made possible.
    """
    conf = copy.deepcopy(conf)

    plugged_by_phy = gen_plugged_by_phy(network.get_filtered_phys(netif_managed))

    # auto assign vlan set to physical interface
    iter_vsTag = iter(aa_lst_vsTag(conf))
    for npst, phy in aa_lst_npst_phy(conf, plugged_by_phy):
        try:
            vsTag = iter_vsTag.next()
        except StopIteration:
            break
        conf['netIfaces'][phy] = vsTag

    # auto assign IP configuration to VLAN
    ipConfTag_iter = iter(aa_lst_ipConfTag(conf))
    for npst, fifn, vsTag, vlanId in aa_lst_npst_fifn_vsTag_vlanId(
        conf, plugged_by_phy
    ):
        try:
            ipConfTag = ipConfTag_iter.next()
        except StopIteration:
            break
        conf['vlans'][vsTag][vlanId] = ipConfTag

    # Auto assign IP configuration to physical interface, generating trivial
    # vlan set as needed.
    iter_npst_phy = iter(aa_lst_npst_phy(conf, plugged_by_phy))
    iter_vsTag = iter_new_vsTag(conf)
    for ipConfTag in ipConfTag_iter:
        try:
            npst, phy = iter_npst_phy.next()
        except StopIteration:
            break
        vsTag = iter_vsTag.next()
        conf['vlans'][vsTag] = {0: ipConfTag}
        conf['netIfaces'][phy] = vsTag

    return conf


def save_configuration_initiate_transaction(conf):
    """
    Save XIVO configuration in a place suitable for the system
    configuration generation transaction, then initiate the transaction but
    do *not* run it.

    The transaction will be completed during the next call of
    transaction_system_configuration() - note that there is such a call at
    system startup.
    """
    save_configuration_for_transaction(conf)
    system.sync_no_oserror()
    os.rename(os.path.join(STORE_BASE, STORE_TMP), os.path.join(STORE_BASE, STORE_NEW))


def save_configuration_perform_generation_transaction(conf):
    """
    Save XIVO configuration in a place suitable for the system
    configuration generation transaction, then initiate and perform the
    transaction.
    """
    save_configuration_initiate_transaction(conf)
    transaction_system_configuration()


def autoattrib():
    """
    Auto VLAN Set and IP Configuration attributions.
    Should be called at server startup, after any potential transaction is
    completed by transactional_generation()
    """
    config = load_current_configuration()
    aaconf = autoattrib_conf(config)
    if aaconf == config:
        return
    save_configuration_perform_generation_transaction(aaconf)
