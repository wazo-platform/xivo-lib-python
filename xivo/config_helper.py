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

from functools import partial


def parse_config_file(config_file_name):
    try:
        with open(config_file_name) as config_file:
            return yaml.load(config_file)
    except IOError as e:
        print('Could not read config file {}: {}'.format(config_file_name, e), file=sys.stderr)
        return {}


def parse_config_dir(directory_name):
    full_path = partial(os.path.join, directory_name)
    try:
        extra_config_filenames = os.listdir(directory_name)
    except OSError as e:
        print('Could not read config dir {}: {}'.format(directory_name, e), file=sys.stderr)
        return []

    return [parse_config_file(full_path(f)) for f in sorted(extra_config_filenames)]
