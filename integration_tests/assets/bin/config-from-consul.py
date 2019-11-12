#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2016-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later


from flask import Flask, jsonify

from xivo.chain_map import ChainMap
from xivo.config_helper import read_config_file_hierarchy

app = Flask('myservice')


_DEFAULT_CONFIG = {
    'config_file': '/etc/config-from-consul/config.yml',
    'extra_config_files': '/etc/config-from-consul/conf.d',
}


def get_config():
    return ChainMap(read_config_file_hierarchy(_DEFAULT_CONFIG), _DEFAULT_CONFIG).data


@app.route('/0.1/config')
def config():
    return jsonify(get_config())


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=6363)
