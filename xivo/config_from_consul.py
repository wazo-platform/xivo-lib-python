# -*- coding: utf-8 -*-
# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import print_function
import argparse
import os
import sys

import consul

import yaml


def get_configuration_from_consul():
    parser = argparse.ArgumentParser(
        description=(
            'Create on-the-fly wazo configuration from Consul key/value storage'
        )
    )
    parser.add_argument(
        "--scheme",
        default=os.getenv("WAZO_CONSUL_SCHEME", "http"),
        help="Scheme to connect to Consul server",
    )
    parser.add_argument(
        "--host",
        default=os.getenv("WAZO_CONSUL_HOST", None),
        help="Host to connect to Consul server",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=os.getenv("WAZO_CONSUL_PORT", "8500"),
        help="Port to connect to Consul server",
    )
    parser.add_argument(
        "--service",
        default=os.getenv("WAZO_CONSUL_SERVICE", "auth"),
        help="root key where configuration is stored",
    )

    args = parser.parse_args()

    if args.host is None:
        print("Neither WAZO_CONSUL_HOST or --host is set, ignoring.", file=sys.stderr)
        return 0

    client = consul.Consul(host=args.host, port=args.port, scheme=args.scheme)
    items = client.kv.get(args.service, recurse=True)
    if not items[1]:
        print("{} does not exists, ignoring.", file=sys.stderr)
        return 0

    config = {}
    for item in items[1]:
        paths = item["Key"].split("/")[1:]
        if not paths:
            continue
        config_loc = config
        for path in paths[:-1]:
            config_loc = config_loc.setdefault(path, {})

        # NOTE(sileht): this assumes we have only dict, no list
        config_loc[paths[-1]] = item["Value"].decode()

    print(yaml.safe_dump(config, default_flow_style=False, explicit_start=True))


if __name__ == '__main__':
    get_configuration_from_consul()
