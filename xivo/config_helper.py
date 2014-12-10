# -*- coding: utf-8 -*-

# Copyright (C) 2014 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from __future__ import print_function

import sys
import os
import yaml

from .chain_map import ChainMap
from functools import partial


def parse_config_file(config_file_name):
    try:
        with open(config_file_name) as config_file:
            return yaml.load(config_file)
    except IOError as e:
        print('Could not read config file {}: {}'.format(config_file_name, e), file=sys.stderr)
        return {}


def parse_config_dir(directory_name):
    '''
    Reads all files in directory_name and returns a list of dictionaries containing
    the parsed yaml content from these files.

    Invalid files are ignored and a message is sent to stderr
    '''
    full_path = partial(os.path.join, directory_name)
    try:
        extra_config_filenames = os.listdir(directory_name)
    except OSError as e:
        print('Could not read config dir {}: {}'.format(directory_name, e), file=sys.stderr)
        return []

    def _config_generator():
        for filename in sorted(extra_config_filenames):
            try:
                yield parse_config_file(full_path(filename))
            except Exception as e:
                print('Could not read config file {}: {}'.format(filename, e), file=sys.stderr)

    return list(_config_generator())


def read_config_file_hierarchy(original_config, config_file_key='config_file', extra_config_dir_key='extra_config_files'):
    '''
    Read a config file and an extra config directory, then return the whole
    config with the following priority:

    extra_config_directory (in alphabetical order)
    config file

    The config file name is taken from original_config[config_file_key].
    The extra config directory name is taken from original_config[extra_config_dir_key].
    '''

    main_config_filename = original_config[config_file_key]
    main_config = parse_config_file(main_config_filename)
    extra_config_file_directory = ChainMap(main_config, original_config)[extra_config_dir_key]
    configs = parse_config_dir(extra_config_file_directory)
    configs.append(main_config)

    return ChainMap(*configs)
