# -*- coding: utf-8 -*-

# Copyright (C) 2014-2015 Avencall
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

from functools import partial
import os
import sys
import subprocess

import yaml

from .chain_map import ChainMap


class _YAMLExecTag(yaml.YAMLObject):

    yaml_tag = u'!exec'

    @classmethod
    def from_yaml(cls, loader, node):
        for key, value in node.value:
            if key.value == 'command':
                return yaml.load(subprocess.check_output(value.value.split(' ')))


class ErrorHandler(object):

    def on_parse_config_file_env_error(self, config_file_name, e):
        pass

    def on_parse_config_dir_env_error(self, directory_name, e):
        pass

    def on_parse_config_dir_parse_exception(self, filename, e):
        pass


class PrintErrorHandler(ErrorHandler):

    def on_parse_config_file_env_error(self, config_file_name, e):
        print('Could not read config file {}: {}'.format(config_file_name, e), file=sys.stderr)

    def on_parse_config_dir_env_error(self, directory_name, e):
        print('Could not read config dir {}: {}'.format(directory_name, e), file=sys.stderr)

    def on_parse_config_dir_parse_exception(self, filename, e):
        print('Could not read config file {}: {}'.format(filename, e), file=sys.stderr)


class ConfigParser(object):

    def __init__(self, error_handler=PrintErrorHandler()):
        self._error_handler = error_handler

    def parse_config_file(self, config_file_name):
        try:
            with open(config_file_name) as config_file:
                data = yaml.load(config_file)
            return data if data else {}
        except EnvironmentError as e:
            self._error_handler.on_parse_config_file_env_error(config_file_name, e)
            return {}

    def parse_config_dir(self, directory_name):
        '''
        Reads all files in directory_name and returns a list of dictionaries containing
        the parsed yaml content from these files.

        Invalid files are ignored and a message is sent to stderr
        '''
        full_path = partial(os.path.join, directory_name)
        try:
            extra_config_filenames = os.listdir(directory_name)
        except EnvironmentError as e:
            self._error_handler.on_parse_config_dir_env_error(directory_name, e)
            return []

        def _config_generator():
            for filename in sorted(extra_config_filenames):
                if filename.startswith('.'):
                    continue

                try:
                    yield self.parse_config_file(full_path(filename))
                except Exception as e:
                    self._error_handler.on_parse_config_dir_parse_exception(filename, e)

        return list(_config_generator())

    def read_config_file_hierarchy(self, original_config, config_file_key='config_file', extra_config_dir_key='extra_config_files'):
        '''
        Read a config file and an extra config directory, then return a dictionary
        containing the config read, aggregated by the following priority:

        1. extra config directory (in alphabetical order)
        2. config file

        The config file name is taken from original_config[config_file_key].
        The extra config directory name is taken from
        config_file[extra_config_dir_key] else original_config[extra_config_dir_key].
        '''

        main_config_filename = original_config[config_file_key]
        main_config = self.parse_config_file(main_config_filename)
        extra_config_file_directory = ChainMap(main_config, original_config)[extra_config_dir_key]
        configs = self.parse_config_dir(extra_config_file_directory)
        configs.append(main_config)

        return ChainMap(*configs)


_config_parser = ConfigParser()

parse_config_file = _config_parser.parse_config_file
parse_config_dir = _config_parser.parse_config_dir
read_config_file_hierarchy = _config_parser.read_config_file_hierarchy
