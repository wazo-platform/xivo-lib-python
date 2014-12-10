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

import os
import random
import string
import tempfile
import unittest

from ..config_helper import parse_config_dir
from ..config_helper import parse_config_file
from ..config_helper import read_config_file_hierarchy
from hamcrest import assert_that
from hamcrest import contains
from hamcrest import equal_to
from mock import patch
from operator import itemgetter
from yaml.parser import ParserError


def _none_existent_filename():
    while True:
        filename = '{}-{}'.format(
            os.path.dirname(__file__),
            ''.join(random.choice(string.lowercase) for _ in xrange(3)))
        if not os.path.exists(filename):
            return filename


def _new_tmp_dir():
    while True:
        suffix = ''.join(random.choice(string.lowercase) for _ in xrange(3))
        dirname = os.path.join(tempfile.gettempdir(), suffix)
        if not os.path.exists(dirname):
            os.mkdir(dirname)
            tempfile.tempdir = dirname
            break
    return dirname


class TestParseConfigFile(unittest.TestCase):

    @patch('__builtin__.print')
    def test_empty_dict_when_no_file_or_directory(self, mocked_print):
        no_such_file = _none_existent_filename()

        result = parse_config_file(no_such_file)

        assert_that(result, equal_to({}))
        printed_message = mocked_print.call_args_list[0]
        assert_that(printed_message.startswith('Could not read config file'))

    def test_invalid_yaml_raises(self):
        content = """ \
        test: [:one :two :3]'
        """

        f = tempfile.NamedTemporaryFile()
        f.writelines(content.split('\n'))
        f.seek(0)

        self.assertRaises(ParserError, parse_config_file, f.name)

    def test_with_valid_yaml(self):
        content = """ \
        test: value
        """

        f = tempfile.NamedTemporaryFile()
        f.writelines(content.split('\n'))
        f.seek(0)

        res = parse_config_file(f.name)

        assert_that(res, equal_to({'test': 'value'}))


class TestParseConfigDir(unittest.TestCase):

    @patch('__builtin__.print')
    def test_no_such_directory(self, mocked_print):
        dirname = _none_existent_filename()

        result = parse_config_dir(dirname)

        assert_that(result, contains())
        printed_message = mocked_print.call_args_list[0]
        assert_that(printed_message.startswith('Could not read config dir'))

    def test_with_only_valid_configs(self):
        dirname = _new_tmp_dir()

        f1 = tempfile.NamedTemporaryFile()
        f1.writelines('test: one')
        f1.seek(0)
        f2 = tempfile.NamedTemporaryFile()
        f2.writelines('test: two')
        f2.seek(0)

        res = parse_config_dir(dirname)

        sorted_files = sorted([{'file': f1.name,
                                'content': {'test': 'one'}},
                               {'file': f2.name,
                                'content': {'test': 'two'}}], key=itemgetter('file'))
        expected = [entry['content'] for entry in sorted_files]
        assert_that(res, contains(*expected))

    @patch('__builtin__.print')
    def test_that_valid_configs_are_returned_when_one_fails(self, mocked_print):
        dirname = _new_tmp_dir()

        f1 = tempfile.NamedTemporaryFile()
        f1.writelines('test: one')
        f1.seek(0)
        f2 = tempfile.NamedTemporaryFile()
        f2.writelines('test: [:one :two]')
        f2.seek(0)

        res = parse_config_dir(dirname)

        assert_that(res, contains({'test': 'one'}))
        printed_message = mocked_print.call_args_list[0]
        assert_that(printed_message.startswith('Could not read config dir'))


class TestReadConfigFileHierarchy(unittest.TestCase):

    @patch('xivo.config_helper.parse_config_file')
    @patch('xivo.config_helper.parse_config_dir')
    def test_that_the_main_config_file_is_read(self, mocked_parse_config_dir, mocked_parse_config_file):
        mocked_parse_config_file.return_value = {'extra_config_files': '/path/to/extra',
                                                 'sentinel': 'from_main_file',
                                                 'main_file_only': True}
        mocked_parse_config_dir.return_value = [{'sentinel': 'from_extra_config'}]
        cli_and_default_config = {
            'config_file': '/path/to/config.yml',
            'extra_config_files': '/original/path/to/extra',
            'sentinel': 'from_default',
        }

        config = read_config_file_hierarchy(cli_and_default_config)

        mocked_parse_config_file.assert_called_once_with('/path/to/config.yml')
        mocked_parse_config_dir.assert_called_once_with('/path/to/extra')

        assert_that(config['sentinel'], equal_to('from_extra_config'))
        assert_that(config['main_file_only'], equal_to(True))
